"""
Unit tests for the TextParserService.
"""
from unittest.mock import Mock, patch

import pytest

from core.services.text_parser import (DiagramType, Entity, EntityType,
                                       ParsedContent, Relationship,
                                       TextParserService)


class TestTextParserService:
    """Test cases for TextParserService."""
    
    @pytest.fixture
    def parser_service(self):
        """Create a TextParserService instance for testing."""
        with patch('spacy.load') as mock_load:
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
        assert entities[0].properties['spacy_label'] == "PERSON"
    
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
        assert entities[0].properties['source'] == 'noun_phrase'
    
    def test_identify_relationships_creates_pattern(self, parser_service):
        """Test relationship identification with 'creates' pattern."""
        service, _ = parser_service
        
        entities = [
            Entity("User", EntityType.ACTOR, {}, 0.8, 0, 4),
            Entity("Order", EntityType.OBJECT, {}, 0.8, 13, 18)
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
            Entity("User", EntityType.ACTOR, {}, 0.8, 25, 29)
        ]
        
        text = "System uses Database and User sends request"
        relationships = service.identify_relationships(text, entities)
        
        # Should find "System uses Database" but not "User sends request" 
        # because "request" is not in entities
        assert len(relationships) == 1
        assert relationships[0].source == "System"
        assert relationships[0].target == "Database"
        assert relationships[0].type == "uses"
    
    def test_determine_diagram_type_erd(self, parser_service):
        """Test ERD diagram type determination."""
        service, _ = parser_service
        
        text = "Database schema with user table and order table"
        entities = [
            Entity("user table", EntityType.DATA, {}, 0.8, 0, 10),
            Entity("order table", EntityType.DATA, {}, 0.8, 15, 26)
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
            Entity("System", EntityType.SYSTEM, {}, 0.8, 22, 28)
        ]
        relationships = [
            Relationship("User", "System", "sends", "Sends", 0.7)
        ]
        
        diagram_type = service.determine_diagram_type(text, entities, relationships)
        
        assert diagram_type == DiagramType.SEQUENCE
    
    def test_determine_diagram_type_class(self, parser_service):
        """Test class diagram type determination."""
        service, _ = parser_service
        
        text = "Animal class and Dog inherits from Animal"
        entities = [
            Entity("Animal", EntityType.OBJECT, {}, 0.8, 0, 6),
            Entity("Dog", EntityType.OBJECT, {}, 0.8, 17, 20)
        ]
        relationships = [
            Relationship("Dog", "Animal", "inherits", "Inherits", 0.7)
        ]
        
        diagram_type = service.determine_diagram_type(text, entities, relationships)
        
        assert diagram_type == DiagramType.CLASS
    
    def test_determine_diagram_type_process(self, parser_service):
        """Test process diagram type determination."""
        service, _ = parser_service
        
        text = "Order processing workflow with validation process"
        entities = [
            Entity("validation process", EntityType.PROCESS, {}, 0.8, 0, 18),
            Entity("order processing", EntityType.PROCESS, {}, 0.8, 19, 35)
        ]
        relationships = []
        
        diagram_type = service.determine_diagram_type(text, entities, relationships)
        
        assert diagram_type == DiagramType.PROCESS
    
    def test_determine_diagram_type_default_flowchart(self, parser_service):
        """Test default flowchart diagram type."""
        service, _ = parser_service
        
        text = "Simple business logic"
        entities = [
            Entity("business logic", EntityType.OBJECT, {}, 0.8, 7, 21)
        ]
        relationships = []
        
        diagram_type = service.determine_diagram_type(text, entities, relationships)
        
        assert diagram_type == DiagramType.FLOWCHART
    
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
            Entity("Order", EntityType.OBJECT, {}, 0.6, 5, 10)
        ]
        relationships = [
            Relationship("User", "Order", "creates", "Creates", 0.7)
        ]
        
        confidence = service._calculate_confidence(entities, relationships)
        
        # Average entity confidence: (0.8 + 0.6) / 2 = 0.7
        # Relationship bonus: 1 * 0.1 = 0.1
        # Total: 0.7 + 0.1 = 0.8
        assert confidence == 0.8
    
    def test_calculate_confidence_max_relationship_bonus(self, parser_service):
        """Test confidence calculation with maximum relationship bonus."""
        service, _ = parser_service
        
        entities = [
            Entity("Entity1", EntityType.OBJECT, {}, 0.5, 0, 7)
        ]
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
        mock_nlp.return_value = mock_doc
        
        text = "User creates order system"
        result = service.parse_text(text)
        
        assert len(result.entities) == 2
        assert len(result.relationships) == 1
        assert result.relationships[0].source == "User"
        assert result.relationships[0].target == "order system"
        assert result.relationships[0].type == "creates"
        assert result.confidence > 0.0
        assert result.suggested_diagram_type in [DiagramType.FLOWCHART, DiagramType.PROCESS]