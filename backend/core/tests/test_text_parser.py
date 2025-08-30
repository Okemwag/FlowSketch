"""
Unit tests for the TextParserService.
"""

from unittest.mock import Mock, patch

import pytest

from core.services.text_parser import (
    DiagramType,
    Entity,
    EntityType,
    ParsedContent,
    Relationship,
    TextParserService,
)


class TestTextParserService:
    """Test cases for TextParserService."""

    @pytest.fixture
    def parser_service(self):
        """Create a TextParserService instance for testing."""
        with patch("spacy.load") as mock_load:
            # Mock spaCy model
            mock_nlp = Mock()
            mock_load.return_value = mock_nlp

            # Create service instance
            service = TextParserService()
            service.nlp = mock_nlp

            return service, mock_nlp

    def test_parse_empty_text(self, parser_service):
        """Test parsing empty or whitespace-only text."""
        service, _ = parser_service

        result = service.parse_text("")

        assert isinstance(result, ParsedContent)
        assert result.entities == []
        assert result.relationships == []
        assert result.suggested_diagram_type == DiagramType.FLOWCHART
        assert result.confidence == 0.0
        assert result.raw_text == ""

    def test_parse_simple_text(self, parser_service):
        """Test parsing simple text with basic entities."""
        service, mock_nlp = parser_service

        # Mock spaCy document
        mock_doc = Mock()
        mock_doc.ents = []
        mock_doc.noun_chunks = []
        mock_nlp.return_value = mock_doc

        text = "User creates order"
        result = service.parse_text(text)

        assert isinstance(result, ParsedContent)
        assert result.raw_text == text
        mock_nlp.assert_called_once_with(text)

    def test_extract_entities_from_named_entities(self, parser_service):
        """Test entity extraction from spaCy named entities."""
        service, mock_nlp = parser_service

        # Mock named entity
        mock_entity = Mock()
        mock_entity.text = "John Doe"
        mock_entity.label_ = "PERSON"
        mock_entity.start_char = 0
        mock_entity.end_char = 8

        mock_doc = Mock()
        mock_doc.ents = [mock_entity]
        mock_doc.noun_chunks = []

        entities = service.extract_entities(mock_doc)

        assert len(entities) == 1
        assert entities[0].name == "John Doe"
        assert entities[0].type == EntityType.ACTOR
        assert entities[0].confidence == 0.8
        assert entities[0].properties["spacy_label"] == "PERSON"

    def test_extract_entities_from_noun_chunks(self, parser_service):
        """Test entity extraction from noun phrases."""
        service, mock_nlp = parser_service

        # Mock noun chunk
        mock_chunk = Mock()
        mock_chunk.text = "user account"
        mock_chunk.start_char = 0
        mock_chunk.end_char = 12

        # Mock tokens in chunk
        mock_token1 = Mock()
        mock_token1.is_stop = False
        mock_token1.is_alpha = True
        mock_token2 = Mock()
        mock_token2.is_stop = False
        mock_token2.is_alpha = True
        mock_chunk.__iter__ = Mock(return_value=iter([mock_token1, mock_token2]))

        mock_doc = Mock()
        mock_doc.ents = []
        mock_doc.noun_chunks = [mock_chunk]

        entities = service.extract_entities(mock_doc)

        assert len(entities) == 1
        assert entities[0].name == "user account"
        assert entities[0].type == EntityType.ACTOR  # Contains 'user'
        assert entities[0].confidence == 0.6
        assert entities[0].properties["source"] == "noun_phrase"

    def test_identify_relationships_creates_pattern(self, parser_service):
        """Test relationship identification with 'creates' pattern."""
        service, _ = parser_service

        entities = [
            Entity("User", EntityType.ACTOR, {}, 0.8, 0, 4),
            Entity("Order", EntityType.OBJECT, {}, 0.8, 13, 18),
        ]

        text = "User creates Order"
        relationships = service.identify_relationships(text, entities)

        assert len(relationships) == 1
        assert relationships[0].source == "User"
        assert relationships[0].target == "Order"
        assert relationships[0].type == "creates"
        assert relationships[0].label == "Creates"
        assert relationships[0].confidence == 0.7

    def test_identify_relationships_multiple_patterns(self, parser_service):
        """Test identification of multiple relationship patterns."""
        service, _ = parser_service

        entities = [
            Entity("System", EntityType.SYSTEM, {}, 0.8, 0, 6),
            Entity("Database", EntityType.SYSTEM, {}, 0.8, 12, 20),
            Entity("User", EntityType.ACTOR, {}, 0.8, 25, 29),
            Entity("Request", EntityType.DATA, {}, 0.8, 30, 37),
        ]

        text = "System uses Database and User sends Request to System"
        relationships = service.identify_relationships(text, entities)

        # Should find multiple relationships
        assert len(relationships) >= 2

        # Check for "System uses Database"
        uses_rel = next((r for r in relationships if r.type == "uses"), None)
        assert uses_rel is not None
        assert uses_rel.source == "System"
        assert uses_rel.target == "Database"

        # Check for sending relationship
        send_rel = next((r for r in relationships if "send" in r.type), None)
        assert send_rel is not None

    def test_determine_diagram_type_erd(self, parser_service):
        """Test ERD diagram type determination."""
        service, _ = parser_service

        text = "Database schema with user table and order table"
        entities = [
            Entity("user table", EntityType.DATA, {}, 0.8, 0, 10),
            Entity("order table", EntityType.DATA, {}, 0.8, 15, 26),
        ]
        relationships = []

        diagram_type = service.determine_diagram_type(text, entities, relationships)

        assert diagram_type == DiagramType.ERD

    def test_determine_diagram_type_sequence(self, parser_service):
        """Test sequence diagram type determination."""
        service, _ = parser_service

        text = "User sends message to System"
        entities = [
            Entity("User", EntityType.ACTOR, {}, 0.8, 0, 4),
            Entity("System", EntityType.SYSTEM, {}, 0.8, 22, 28),
        ]
        relationships = [Relationship("User", "System", "sends", "Sends", 0.7)]

        diagram_type = service.determine_diagram_type(text, entities, relationships)

        assert diagram_type == DiagramType.SEQUENCE

    def test_determine_diagram_type_class(self, parser_service):
        """Test class diagram type determination."""
        service, _ = parser_service

        text = "Animal class and Dog inherits from Animal"
        entities = [
            Entity("Animal", EntityType.OBJECT, {}, 0.8, 0, 6),
            Entity("Dog", EntityType.OBJECT, {}, 0.8, 17, 20),
        ]
        relationships = [Relationship("Dog", "Animal", "inherits", "Inherits", 0.7)]

        diagram_type = service.determine_diagram_type(text, entities, relationships)

        assert diagram_type == DiagramType.CLASS

    def test_determine_diagram_type_process(self, parser_service):
        """Test process diagram type determination."""
        service, _ = parser_service

        text = "Order processing workflow with validation process"
        entities = [
            Entity("validation process", EntityType.PROCESS, {}, 0.8, 0, 18),
            Entity("order processing", EntityType.PROCESS, {}, 0.8, 19, 35),
        ]
        relationships = []

        diagram_type = service.determine_diagram_type(text, entities, relationships)

        assert diagram_type == DiagramType.PROCESS

    def test_determine_diagram_type_default_flowchart(self, parser_service):
        """Test default flowchart diagram type."""
        service, _ = parser_service

        text = "Simple business logic"
        entities = [Entity("business logic", EntityType.OBJECT, {}, 0.8, 7, 21)]
        relationships = []

        diagram_type = service.determine_diagram_type(text, entities, relationships)

        assert diagram_type == DiagramType.FLOWCHART

    def test_advanced_erd_detection(self, parser_service):
        """Test advanced ERD detection with multiple indicators."""
        service, _ = parser_service

        text = "Database schema with user table containing primary key and foreign key relationships to order table"
        entities = [
            Entity("user table", EntityType.DATA, {}, 0.8, 0, 10),
            Entity("order table", EntityType.DATA, {}, 0.8, 15, 26),
            Entity("primary key", EntityType.DATA, {}, 0.8, 30, 41),
            Entity("foreign key", EntityType.DATA, {}, 0.8, 45, 56),
        ]
        relationships = [
            Relationship("user table", "order table", "references", "References", 0.8)
        ]

        diagram_type = service.determine_diagram_type(text, entities, relationships)

        assert diagram_type == DiagramType.ERD

    def test_advanced_sequence_detection(self, parser_service):
        """Test advanced sequence diagram detection."""
        service, _ = parser_service

        text = "User sends authentication request to Server, Server validates credentials and sends response back"
        entities = [
            Entity("User", EntityType.ACTOR, {}, 0.8, 0, 4),
            Entity("Server", EntityType.SYSTEM, {}, 0.8, 10, 16),
            Entity("authentication request", EntityType.DATA, {}, 0.8, 20, 42),
            Entity("response", EntityType.DATA, {}, 0.8, 50, 58),
        ]
        relationships = [
            Relationship("User", "Server", "sends", "Sends", 0.8),
            Relationship("Server", "User", "sends", "Sends", 0.8),
        ]

        diagram_type = service.determine_diagram_type(text, entities, relationships)

        assert diagram_type == DiagramType.SEQUENCE

    def test_advanced_class_detection(self, parser_service):
        """Test advanced class diagram detection."""
        service, _ = parser_service

        text = "Animal class with Dog class inheriting from Animal and implementing Mammal interface"
        entities = [
            Entity("Animal", EntityType.OBJECT, {}, 0.8, 0, 6),
            Entity("Dog", EntityType.OBJECT, {}, 0.8, 17, 20),
            Entity("Mammal", EntityType.OBJECT, {}, 0.8, 30, 36),
        ]
        relationships = [
            Relationship("Dog", "Animal", "inherits", "Inherits", 0.9),
            Relationship("Dog", "Mammal", "implements", "Implements", 0.8),
        ]

        diagram_type = service.determine_diagram_type(text, entities, relationships)

        assert diagram_type == DiagramType.CLASS

    def test_advanced_process_detection(self, parser_service):
        """Test advanced process diagram detection."""
        service, _ = parser_service

        text = "Order processing workflow: first validation process, then payment process, finally fulfillment process"
        entities = [
            Entity("validation process", EntityType.PROCESS, {}, 0.8, 0, 18),
            Entity("payment process", EntityType.PROCESS, {}, 0.8, 25, 40),
            Entity("fulfillment process", EntityType.PROCESS, {}, 0.8, 50, 69),
        ]
        relationships = [
            Relationship(
                "validation process", "payment process", "flows_to", "Flows To", 0.8
            ),
            Relationship(
                "payment process", "fulfillment process", "flows_to", "Flows To", 0.8
            ),
        ]

        diagram_type = service.determine_diagram_type(text, entities, relationships)

        assert diagram_type == DiagramType.PROCESS

    def test_diagram_type_suggestions(self, parser_service):
        """Test getting all diagram type suggestions with scores."""
        service, _ = parser_service

        text = "User interacts with system database"
        entities = [
            Entity("User", EntityType.ACTOR, {}, 0.8, 0, 4),
            Entity("system", EntityType.SYSTEM, {}, 0.8, 20, 26),
            Entity("database", EntityType.SYSTEM, {}, 0.8, 27, 35),
        ]
        relationships = [
            Relationship("User", "system", "interacts_with", "Interacts With", 0.7)
        ]

        suggestions = service.get_diagram_type_suggestions(
            text, entities, relationships
        )

        # Should return all diagram types with scores
        assert isinstance(suggestions, dict)
        assert len(suggestions) == 5
        assert all(isinstance(score, float) for score in suggestions.values())
        assert all(0.0 <= score <= 1.0 for score in suggestions.values())

        # Should be sorted by confidence (highest first)
        scores = list(suggestions.values())
        assert scores == sorted(scores, reverse=True)

    def test_mixed_content_diagram_selection(self, parser_service):
        """Test diagram type selection with mixed content indicators."""
        service, _ = parser_service

        text = "Database table stores user data and processes workflow steps"
        entities = [
            Entity("Database table", EntityType.DATA, {}, 0.8, 0, 14),
            Entity("user data", EntityType.DATA, {}, 0.8, 22, 31),
            Entity("workflow steps", EntityType.PROCESS, {}, 0.8, 45, 59),
        ]
        relationships = [
            Relationship("Database table", "user data", "stores", "Stores", 0.8)
        ]

        diagram_type = service.determine_diagram_type(text, entities, relationships)

        # Should choose the type with highest score (likely ERD due to database keywords)
        assert diagram_type in [
            DiagramType.ERD,
            DiagramType.PROCESS,
            DiagramType.FLOWCHART,
        ]

    def test_confidence_threshold_fallback(self, parser_service):
        """Test fallback to flowchart when no type has strong confidence."""
        service, _ = parser_service

        text = "Some generic content without specific indicators"
        entities = [Entity("content", EntityType.OBJECT, {}, 0.8, 5, 12)]
        relationships = []

        diagram_type = service.determine_diagram_type(text, entities, relationships)

        # Should fallback to flowchart when confidence is low
        assert diagram_type == DiagramType.FLOWCHART

    def test_enhanced_erd_detection(self, parser_service):
        """Test enhanced ERD detection with scoring."""
        service, _ = parser_service

        text = "User table contains user information with primary key. Order table has foreign key to User table."
        entities = [
            Entity("User table", EntityType.DATA, {}, 0.8, 0, 10),
            Entity("Order table", EntityType.DATA, {}, 0.8, 50, 61),
            Entity("user information", EntityType.DATA, {}, 0.8, 20, 36),
        ]
        relationships = [
            Relationship("User table", "user information", "contains", "Contains", 0.7),
            Relationship("Order table", "User table", "references", "References", 0.8),
        ]

        diagram_type = service.determine_diagram_type(text, entities, relationships)
        assert diagram_type == DiagramType.ERD

        # Test scoring method directly
        erd_score = service._calculate_erd_score(text, entities, relationships)
        assert erd_score > 0.5

    def test_enhanced_sequence_detection(self, parser_service):
        """Test enhanced sequence diagram detection."""
        service, _ = parser_service

        text = "User sends request to Authentication Service. Service returns response with token."
        entities = [
            Entity("User", EntityType.ACTOR, {}, 0.8, 0, 4),
            Entity("Authentication Service", EntityType.SYSTEM, {}, 0.8, 20, 42),
            Entity("token", EntityType.DATA, {}, 0.8, 70, 75),
        ]
        relationships = [
            Relationship("User", "Authentication Service", "sends", "Sends", 0.8),
            Relationship("Authentication Service", "User", "returns", "Returns", 0.7),
        ]

        diagram_type = service.determine_diagram_type(text, entities, relationships)
        assert diagram_type == DiagramType.SEQUENCE

        # Test scoring method
        sequence_score = service._calculate_sequence_score(
            text, entities, relationships
        )
        assert sequence_score > 0.4

    def test_enhanced_class_detection(self, parser_service):
        """Test enhanced class diagram detection."""
        service, _ = parser_service

        text = "Animal class with methods. Dog class inherits from Animal and implements Mammal interface."
        entities = [
            Entity("Animal class", EntityType.OBJECT, {}, 0.8, 0, 12),
            Entity("Dog class", EntityType.OBJECT, {}, 0.8, 30, 39),
            Entity("Mammal interface", EntityType.OBJECT, {}, 0.8, 70, 86),
        ]
        relationships = [
            Relationship("Dog class", "Animal class", "inherits", "Inherits", 0.9),
            Relationship(
                "Dog class", "Mammal interface", "implements", "Implements", 0.8
            ),
        ]

        diagram_type = service.determine_diagram_type(text, entities, relationships)
        assert diagram_type == DiagramType.CLASS

        # Test scoring method
        class_score = service._calculate_class_score(text, entities, relationships)
        assert class_score > 0.5

    def test_enhanced_process_detection(self, parser_service):
        """Test enhanced process diagram detection."""
        service, _ = parser_service

        text = "Order processing workflow starts with validation step, then payment process, finally fulfillment."
        entities = [
            Entity("validation step", EntityType.PROCESS, {}, 0.8, 40, 55),
            Entity("payment process", EntityType.PROCESS, {}, 0.8, 62, 78),
            Entity("fulfillment", EntityType.PROCESS, {}, 0.8, 88, 99),
        ]
        relationships = [
            Relationship(
                "validation step", "payment process", "precedes", "Precedes", 0.7
            ),
            Relationship("payment process", "fulfillment", "precedes", "Precedes", 0.7),
        ]

        diagram_type = service.determine_diagram_type(text, entities, relationships)
        assert diagram_type == DiagramType.PROCESS

        # Test scoring method
        process_score = service._calculate_process_score(text, entities, relationships)
        assert process_score > 0.5

    def test_diagram_type_suggestions(self, parser_service):
        """Test getting all diagram type suggestions with scores."""
        service, _ = parser_service

        text = "User interacts with System to process Order data"
        entities = [
            Entity("User", EntityType.ACTOR, {}, 0.8, 0, 4),
            Entity("System", EntityType.SYSTEM, {}, 0.8, 20, 26),
            Entity("Order data", EntityType.DATA, {}, 0.8, 38, 48),
        ]
        relationships = [
            Relationship("User", "System", "interacts_with", "Interacts With", 0.7),
            Relationship("System", "Order data", "processes", "Processes", 0.8),
        ]

        suggestions = service.get_diagram_type_suggestions(
            text, entities, relationships
        )

        # Should return all diagram types with scores
        assert len(suggestions) == 5
        assert "erd" in suggestions
        assert "sequence" in suggestions
        assert "class" in suggestions
        assert "process" in suggestions
        assert "flowchart" in suggestions

        # Scores should be between 0 and 1
        for score in suggestions.values():
            assert 0 <= score <= 1

        # Should be sorted by confidence (highest first)
        scores = list(suggestions.values())
        assert scores == sorted(scores, reverse=True)

    def test_mixed_content_scoring(self, parser_service):
        """Test scoring with mixed content that could fit multiple diagram types."""
        service, _ = parser_service

        text = "User class creates Order object and stores it in Database table"
        entities = [
            Entity("User class", EntityType.OBJECT, {}, 0.8, 0, 10),
            Entity("Order object", EntityType.OBJECT, {}, 0.8, 19, 31),
            Entity("Database table", EntityType.DATA, {}, 0.8, 50, 64),
        ]
        relationships = [
            Relationship("User class", "Order object", "creates", "Creates", 0.8),
            Relationship(
                "Order object", "Database table", "stored_in", "Stored In", 0.7
            ),
        ]

        suggestions = service.get_diagram_type_suggestions(
            text, entities, relationships
        )

        # Should have reasonable scores for multiple types
        assert suggestions["class"] > 0.3  # Has class-related content
        assert suggestions["erd"] > 0.2  # Has database content
        assert suggestions["flowchart"] > 0.2  # General fallback

    def test_classify_entity_type_process_keywords(self, parser_service):
        """Test entity type classification with process keywords."""
        service, _ = parser_service

        entity_type = service._classify_entity_type("create user")
        assert entity_type == EntityType.PROCESS

        entity_type = service._classify_entity_type("validation process")
        assert entity_type == EntityType.PROCESS

    def test_classify_entity_type_system_keywords(self, parser_service):
        """Test entity type classification with system keywords."""
        service, _ = parser_service

        entity_type = service._classify_entity_type("payment service")
        assert entity_type == EntityType.SYSTEM

        entity_type = service._classify_entity_type("user database")
        assert entity_type == EntityType.SYSTEM

    def test_classify_entity_type_data_keywords(self, parser_service):
        """Test entity type classification with data keywords."""
        service, _ = parser_service

        entity_type = service._classify_entity_type("user data")
        assert entity_type == EntityType.DATA

        entity_type = service._classify_entity_type("order information")
        assert entity_type == EntityType.DATA

    def test_classify_entity_type_actor_keywords(self, parser_service):
        """Test entity type classification with actor keywords."""
        service, _ = parser_service

        entity_type = service._classify_entity_type("system user")
        assert entity_type == EntityType.ACTOR

        entity_type = service._classify_entity_type("customer account")
        assert entity_type == EntityType.ACTOR

    def test_classify_entity_type_spacy_labels(self, parser_service):
        """Test entity type classification using spaCy labels."""
        service, _ = parser_service

        entity_type = service._classify_entity_type("John Smith", "PERSON")
        assert entity_type == EntityType.ACTOR

        entity_type = service._classify_entity_type("Microsoft", "ORG")
        assert entity_type == EntityType.SYSTEM

        entity_type = service._classify_entity_type("Conference", "EVENT")
        assert entity_type == EntityType.EVENT

    def test_classify_entity_type_default(self, parser_service):
        """Test default entity type classification."""
        service, _ = parser_service

        entity_type = service._classify_entity_type("random thing")
        assert entity_type == EntityType.OBJECT

    def test_calculate_confidence_no_entities(self, parser_service):
        """Test confidence calculation with no entities."""
        service, _ = parser_service

        confidence = service._calculate_confidence([], [])
        assert confidence == 0.0

    def test_calculate_confidence_with_entities_and_relationships(self, parser_service):
        """Test confidence calculation with entities and relationships."""
        service, _ = parser_service

        entities = [
            Entity("User", EntityType.ACTOR, {}, 0.8, 0, 4),
            Entity("Order", EntityType.OBJECT, {}, 0.6, 5, 10),
        ]
        relationships = [Relationship("User", "Order", "creates", "Creates", 0.7)]

        confidence = service._calculate_confidence(entities, relationships)

        # Average entity confidence: (0.8 + 0.6) / 2 = 0.7
        # Relationship bonus: 1 * 0.1 = 0.1
        # Total: 0.7 + 0.1 = 0.8
        assert confidence == 0.8

    def test_calculate_confidence_max_relationship_bonus(self, parser_service):
        """Test confidence calculation with maximum relationship bonus."""
        service, _ = parser_service

        entities = [Entity("Entity1", EntityType.OBJECT, {}, 0.5, 0, 7)]
        # Create 5 relationships to test max bonus of 0.3
        relationships = [
            Relationship("Entity1", "Entity2", "rel1", "Rel1", 0.7),
            Relationship("Entity1", "Entity3", "rel2", "Rel2", 0.7),
            Relationship("Entity1", "Entity4", "rel3", "Rel3", 0.7),
            Relationship("Entity1", "Entity5", "rel4", "Rel4", 0.7),
            Relationship("Entity1", "Entity6", "rel5", "Rel5", 0.7),
        ]

        confidence = service._calculate_confidence(entities, relationships)

        # Entity confidence: 0.5
        # Relationship bonus: min(5 * 0.1, 0.3) = 0.3
        # Total: 0.5 + 0.3 = 0.8
        assert confidence == 0.8

    def test_enhanced_relationship_patterns(self, parser_service):
        """Test enhanced relationship pattern detection."""
        service, _ = parser_service

        entities = [
            Entity("Payment Service", EntityType.SYSTEM, {}, 0.8, 0, 15),
            Entity("Order", EntityType.DATA, {}, 0.8, 20, 25),
            Entity("Database", EntityType.SYSTEM, {}, 0.8, 30, 38),
        ]

        text = "Payment Service processes Order and stores data in Database"
        relationships = service.identify_relationships(text, entities)

        # Should find processing and storage relationships
        assert len(relationships) >= 1

        # Check for processing relationship
        process_rel = next((r for r in relationships if r.type == "processes"), None)
        assert process_rel is not None
        assert process_rel.source == "Payment Service"
        assert process_rel.target == "Order"

    def test_contextual_relationship_detection(self, parser_service):
        """Test contextual relationship pattern detection."""
        service, _ = parser_service

        entities = [
            Entity("User Login", EntityType.PROCESS, {}, 0.8, 0, 10),
            Entity("Dashboard", EntityType.SYSTEM, {}, 0.8, 15, 24),
            Entity("Validation", EntityType.PROCESS, {}, 0.8, 30, 40),
        ]

        text = "After User Login, then Dashboard is displayed. Before Validation, User Login must complete."
        relationships = service.identify_relationships(text, entities)

        # Should find temporal relationships
        assert len(relationships) >= 1

        # Check for temporal relationship
        temporal_rel = next(
            (r for r in relationships if r.type in ["follows", "precedes"]), None
        )
        assert temporal_rel is not None

    def test_fuzzy_entity_matching(self, parser_service):
        """Test fuzzy matching of entity names in relationships."""
        service, _ = parser_service

        entities = [
            Entity("User Account", EntityType.OBJECT, {}, 0.8, 0, 12),
            Entity("Authentication Service", EntityType.SYSTEM, {}, 0.8, 15, 37),
        ]

        text = "User creates account using Authentication Service"
        relationships = service.identify_relationships(text, entities)

        # Should match "User" to "User Account" and find relationship
        assert len(relationships) >= 1

    def test_bidirectional_relationship_detection(self, parser_service):
        """Test detection of bidirectional relationships."""
        service, _ = parser_service

        entities = [
            Entity("Client", EntityType.SYSTEM, {}, 0.8, 0, 6),
            Entity("Server", EntityType.SYSTEM, {}, 0.8, 10, 16),
            Entity("Response", EntityType.DATA, {}, 0.8, 20, 28),
        ]

        text = "Client sends request to Server and Server sends Response back to Client"
        relationships = service.identify_relationships(text, entities)

        # Should find bidirectional communication
        assert len(relationships) >= 1

    def test_relationship_deduplication(self, parser_service):
        """Test deduplication of similar relationships."""
        service, _ = parser_service

        entities = [
            Entity("System", EntityType.SYSTEM, {}, 0.8, 0, 6),
            Entity("Database", EntityType.SYSTEM, {}, 0.8, 10, 18),
        ]

        text = "System uses Database. System utilizes Database for storage."
        relationships = service.identify_relationships(text, entities)

        # Should deduplicate similar relationships
        uses_relationships = [r for r in relationships if r.type == "uses"]
        assert len(uses_relationships) <= 1  # Should be deduplicated

    def test_complex_sentence_parsing(self, parser_service):
        """Test parsing of complex sentences with multiple relationships."""
        service, _ = parser_service

        entities = [
            Entity("User", EntityType.ACTOR, {}, 0.8, 0, 4),
            Entity("Order", EntityType.DATA, {}, 0.8, 10, 15),
            Entity("Payment System", EntityType.SYSTEM, {}, 0.8, 20, 34),
            Entity("Inventory", EntityType.SYSTEM, {}, 0.8, 40, 49),
            Entity("Email Service", EntityType.SYSTEM, {}, 0.8, 55, 68),
        ]

        text = (
            "When User creates Order, Payment System validates payment, "
            "Inventory is updated, and Email Service sends confirmation."
        )
        relationships = service.identify_relationships(text, entities)

        # Should find multiple relationships in complex sentence
        assert len(relationships) >= 2

    def test_integration_parse_realistic_text(self, parser_service):
        """Integration test with realistic text input."""
        service, mock_nlp = parser_service

        # Mock spaCy processing
        mock_entity = Mock()
        mock_entity.text = "User"
        mock_entity.label_ = "PERSON"
        mock_entity.start_char = 0
        mock_entity.end_char = 4

        mock_chunk = Mock()
        mock_chunk.text = "order system"
        mock_chunk.start_char = 13
        mock_chunk.end_char = 25

        mock_token1 = Mock()
        mock_token1.is_stop = False
        mock_token1.is_alpha = True
        mock_token2 = Mock()
        mock_token2.is_stop = False
        mock_token2.is_alpha = True
        mock_chunk.__iter__ = Mock(return_value=iter([mock_token1, mock_token2]))

        mock_doc = Mock()
        mock_doc.ents = [mock_entity]
        mock_doc.noun_chunks = [mock_chunk]
        mock_doc.sents = []  # Mock sentences for dependency parsing
        mock_nlp.return_value = mock_doc

        text = "User creates order system"
        result = service.parse_text(text)

        assert len(result.entities) == 2
        assert len(result.relationships) >= 1
        assert result.confidence > 0.0
        assert result.suggested_diagram_type in [
            DiagramType.FLOWCHART,
            DiagramType.PROCESS,
        ]
        assert "diagram_type_suggestions" in result.__dict__
        assert len(result.diagram_type_suggestions) == 5
