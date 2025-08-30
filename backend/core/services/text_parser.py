"""
Text parsing service for extracting
entities and relationships from unstructured text.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import spacy


class EntityType(Enum):
    """Entity types that can be extracted from text."""

    OBJECT = "object"
    PROCESS = "process"
    ACTOR = "actor"
    DATA = "data"
    SYSTEM = "system"
    EVENT = "event"


class DiagramType(Enum):
    """Supported diagram types."""

    FLOWCHART = "flowchart"
    ERD = "erd"
    SEQUENCE = "sequence"
    CLASS = "class"
    PROCESS = "process"


@dataclass
class Entity:
    """Represents an extracted entity."""

    name: str
    type: EntityType
    properties: Dict[str, Any]
    confidence: float
    start_pos: int
    end_pos: int


@dataclass
class Relationship:
    """Represents a relationship between entities."""

    source: str
    target: str
    type: str
    label: str
    confidence: float


@dataclass
class ParsedContent:
    """Container for parsed text content."""

    entities: List[Entity]
    relationships: List[Relationship]
    suggested_diagram_type: DiagramType
    diagram_type_suggestions: Dict[str, float]
    confidence: float
    raw_text: str


class TextParserService:
    """Service for parsing unstructured text and extracting entities and relationships."""

    def __init__(self):
        """Initialize the text parser with spaCy model."""
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            raise RuntimeError(
                "spaCy English model not found. Please install it with: "
                "python -m spacy download en_core_web_sm"
            )

        # Process-related keywords for entity classification
        self.process_keywords = {
            "create",
            "generate",
            "process",
            "handle",
            "manage",
            "execute",
            "run",
            "start",
            "stop",
            "finish",
            "complete",
            "validate",
            "authenticate",
            "authorize",
            "send",
            "receive",
            "update",
            "delete",
            "save",
            "load",
            "transform",
            "convert",
        }

        # System-related keywords
        self.system_keywords = {
            "system",
            "service",
            "api",
            "database",
            "server",
            "client",
            "application",
            "platform",
            "interface",
            "module",
            "component",
        }

        # Data-related keywords
        self.data_keywords = {
            "data",
            "information",
            "record",
            "file",
            "document",
            "report",
            "message",
            "request",
            "response",
            "payload",
            "schema",
        }

        # Enhanced relationship patterns with more sophisticated detection
        self.relationship_patterns = [
            # Creation relationships
            (
                r"\b(\w+(?:\s+\w+)*)\s+(?:creates?|generates?|produces?|builds?|makes?)\s+(\w+(?:\s+\w+)*)",
                "creates",
            ),
            (
                r"\b(\w+(?:\s+\w+)*)\s+(?:is\s+)?(?:created|generated|produced|built|made)\s+by\s+(\w+(?:\s+\w+)*)",
                "created_by",
            ),
            # Usage relationships
            (
                r"\b(\w+(?:\s+\w+)*)\s+(?:uses?|utilizes?|employs?|leverages?)\s+(\w+(?:\s+\w+)*)",
                "uses",
            ),
            (
                r"\b(\w+(?:\s+\w+)*)\s+(?:is\s+)?(?:used|utilized|employed)\s+by\s+(\w+(?:\s+\w+)*)",
                "used_by",
            ),
            # Communication relationships
            (
                r"\b(\w+(?:\s+\w+)*)\s+(?:sends?|transmits?|delivers?|forwards?)\s+(\w+(?:\s+\w+)*)\s+to\s+(\w+(?:\s+\w+)*)",
                "sends_to",
            ),
            (
                r"\b(\w+(?:\s+\w+)*)\s+(?:receives?|gets?|obtains?|accepts?)\s+(\w+(?:\s+\w+)*)\s+from\s+(\w+(?:\s+\w+)*)",
                "receives_from",
            ),
            (
                r"\b(\w+(?:\s+\w+)*)\s+(?:communicates?\s+with|interacts?\s+with)\s+(\w+(?:\s+\w+)*)",
                "communicates_with",
            ),
            # Containment relationships
            (
                r"\b(\w+(?:\s+\w+)*)\s+(?:contains?|includes?|has|holds?)\s+(\w+(?:\s+\w+)*)",
                "contains",
            ),
            (
                r"\b(\w+(?:\s+\w+)*)\s+(?:is\s+)?(?:contained|included)\s+in\s+(\w+(?:\s+\w+)*)",
                "contained_in",
            ),
            (
                r"\b(\w+(?:\s+\w+)*)\s+(?:belongs?\s+to|is\s+part\s+of)\s+(\w+(?:\s+\w+)*)",
                "belongs_to",
            ),
            # Dependency relationships
            (
                r"\b(\w+(?:\s+\w+)*)\s+(?:depends?\s+on|requires?|needs?)\s+(\w+(?:\s+\w+)*)",
                "depends_on",
            ),
            (
                r"\b(\w+(?:\s+\w+)*)\s+(?:is\s+)?(?:required|needed)\s+by\s+(\w+(?:\s+\w+)*)",
                "required_by",
            ),
            # Inheritance relationships
            (
                r"\b(\w+(?:\s+\w+)*)\s+(?:inherits?\s+from|extends?|derives?\s+from)\s+(\w+(?:\s+\w+)*)",
                "inherits",
            ),
            (
                r"\b(\w+(?:\s+\w+)*)\s+(?:is\s+a\s+(?:type\s+of|kind\s+of|subclass\s+of))\s+(\w+(?:\s+\w+)*)",
                "is_a",
            ),
            (r"\b(\w+(?:\s+\w+)*)\s+(?:implements?)\s+(\w+(?:\s+\w+)*)", "implements"),
            # Flow relationships
            (
                r"\b(\w+(?:\s+\w+)*)\s+(?:flows?\s+to|goes?\s+to|moves?\s+to|proceeds?\s+to)\s+(\w+(?:\s+\w+)*)",
                "flows_to",
            ),
            (
                r"\b(\w+(?:\s+\w+)*)\s+(?:follows?|comes?\s+after)\s+(\w+(?:\s+\w+)*)",
                "follows",
            ),
            (
                r"\b(\w+(?:\s+\w+)*)\s+(?:precedes?|comes?\s+before)\s+(\w+(?:\s+\w+)*)",
                "precedes",
            ),
            # Association relationships
            (
                r"\b(\w+(?:\s+\w+)*)\s+(?:is\s+)?(?:associated\s+with|related\s+to|connected\s+to|linked\s+to)\s+(\w+(?:\s+\w+)*)",
                "associated_with",
            ),
            (
                r"\b(\w+(?:\s+\w+)*)\s+(?:manages?|controls?|oversees?)\s+(\w+(?:\s+\w+)*)",
                "manages",
            ),
            (
                r"\b(\w+(?:\s+\w+)*)\s+(?:is\s+)?(?:managed|controlled|overseen)\s+by\s+(\w+(?:\s+\w+)*)",
                "managed_by",
            ),
            # Process relationships
            (
                r"\b(\w+(?:\s+\w+)*)\s+(?:processes?|handles?|executes?)\s+(\w+(?:\s+\w+)*)",
                "processes",
            ),
            (
                r"\b(\w+(?:\s+\w+)*)\s+(?:is\s+)?(?:processed|handled|executed)\s+by\s+(\w+(?:\s+\w+)*)",
                "processed_by",
            ),
            (
                r"\b(\w+(?:\s+\w+)*)\s+(?:triggers?|initiates?|starts?)\s+(\w+(?:\s+\w+)*)",
                "triggers",
            ),
            (
                r"\b(\w+(?:\s+\w+)*)\s+(?:is\s+)?(?:triggered|initiated|started)\s+by\s+(\w+(?:\s+\w+)*)",
                "triggered_by",
            ),
            # Storage relationships
            (
                r"\b(\w+(?:\s+\w+)*)\s+(?:stores?|saves?|persists?)\s+(\w+(?:\s+\w+)*)",
                "stores",
            ),
            (
                r"\b(\w+(?:\s+\w+)*)\s+(?:is\s+)?(?:stored|saved|persisted)\s+in\s+(\w+(?:\s+\w+)*)",
                "stored_in",
            ),
            # Validation relationships
            (
                r"\b(\w+(?:\s+\w+)*)\s+(?:validates?|verifies?|checks?)\s+(\w+(?:\s+\w+)*)",
                "validates",
            ),
            (
                r"\b(\w+(?:\s+\w+)*)\s+(?:is\s+)?(?:validated|verified|checked)\s+by\s+(\w+(?:\s+\w+)*)",
                "validated_by",
            ),
        ]

        # Contextual relationship indicators
        self.contextual_patterns = [
            # Temporal relationships
            (
                r"\b(?:after|once|when)\s+(\w+(?:\s+\w+)*)[,\s]+(?:then\s+)?(\w+(?:\s+\w+)*)",
                "follows",
            ),
            (
                r"\b(?:before|prior\s+to)\s+(\w+(?:\s+\w+)*)[,\s]+(\w+(?:\s+\w+)*)",
                "precedes",
            ),
            (
                r"\b(?:during|while)\s+(\w+(?:\s+\w+)*)[,\s]+(\w+(?:\s+\w+)*)",
                "concurrent_with",
            ),
            # Conditional relationships
            (
                r"\bif\s+(\w+(?:\s+\w+)*)[,\s]+(?:then\s+)?(\w+(?:\s+\w+)*)",
                "conditional",
            ),
            (r"\bunless\s+(\w+(?:\s+\w+)*)[,\s]+(\w+(?:\s+\w+)*)", "unless"),
            # Causal relationships
            (
                r"\b(\w+(?:\s+\w+)*)\s+(?:causes?|results?\s+in|leads?\s+to)\s+(\w+(?:\s+\w+)*)",
                "causes",
            ),
            (
                r"\b(\w+(?:\s+\w+)*)\s+(?:is\s+)?(?:caused|resulted)\s+by\s+(\w+(?:\s+\w+)*)",
                "caused_by",
            ),
        ]

    def parse_text(self, text: str) -> ParsedContent:
        """
        Parse unstructured text and extract entities, relationships, and suggest diagram type.

        Args:
            text: The input text to parse

        Returns:
            ParsedContent object with extracted information
        """
        if not text or not text.strip():
            return ParsedContent(
                entities=[],
                relationships=[],
                suggested_diagram_type=DiagramType.FLOWCHART,
                diagram_type_suggestions={
                    "flowchart": 0.3,
                    "erd": 0.0,
                    "sequence": 0.0,
                    "class": 0.0,
                    "process": 0.0,
                },
                confidence=0.0,
                raw_text=text,
            )

        # Process text with spaCy
        doc = self.nlp(text)

        # Extract entities
        entities = self.extract_entities(doc)

        # Extract relationships
        relationships = self.identify_relationships(text, entities)

        # Determine diagram type
        diagram_type = self.determine_diagram_type(text, entities, relationships)

        # Get all diagram type suggestions with scores
        diagram_suggestions = self.get_diagram_type_suggestions(
            text, entities, relationships
        )

        # Calculate overall confidence
        confidence = self._calculate_confidence(entities, relationships)

        return ParsedContent(
            entities=entities,
            relationships=relationships,
            suggested_diagram_type=diagram_type,
            diagram_type_suggestions=diagram_suggestions,
            confidence=confidence,
            raw_text=text,
        )

    def extract_entities(self, doc) -> List[Entity]:
        """
        Extract entities from spaCy processed document.

        Args:
            doc: spaCy processed document

        Returns:
            List of extracted entities
        """
        entities = []
        processed_entities = set()  # Avoid duplicates

        # Extract named entities
        for ent in doc.ents:
            if ent.label_ in ["PERSON", "ORG", "PRODUCT", "EVENT"]:
                entity_name = ent.text.strip()
                if entity_name and entity_name.lower() not in processed_entities:
                    entity_type = self._classify_entity_type(entity_name, ent.label_)
                    entities.append(
                        Entity(
                            name=entity_name,
                            type=entity_type,
                            properties={"spacy_label": ent.label_},
                            confidence=0.8,
                            start_pos=ent.start_char,
                            end_pos=ent.end_char,
                        )
                    )
                    processed_entities.add(entity_name.lower())

        # Extract noun phrases as potential entities
        for chunk in doc.noun_chunks:
            entity_name = chunk.text.strip()
            if (
                entity_name
                and len(entity_name.split()) <= 3  # Limit to reasonable length
                and entity_name.lower() not in processed_entities
                and not any(token.is_stop for token in chunk if not token.is_alpha)
            ):

                entity_type = self._classify_entity_type(entity_name)
                entities.append(
                    Entity(
                        name=entity_name,
                        type=entity_type,
                        properties={"source": "noun_phrase"},
                        confidence=0.6,
                        start_pos=chunk.start_char,
                        end_pos=chunk.end_char,
                    )
                )
                processed_entities.add(entity_name.lower())

        return entities

    def identify_relationships(
        self, text: str, entities: List[Entity]
    ) -> List[Relationship]:
        """
        Identify relationships between entities using advanced pattern matching and NLP.

        Args:
            text: Original text
            entities: List of extracted entities

        Returns:
            List of identified relationships
        """
        relationships = []
        entity_names = {entity.name.lower(): entity.name for entity in entities}

        # Create entity mapping for fuzzy matching
        entity_variations = self._create_entity_variations(entities)

        # Apply direct relationship patterns
        relationships.extend(
            self._extract_direct_relationships(text, entity_names, entity_variations)
        )

        # Apply contextual patterns
        relationships.extend(
            self._extract_contextual_relationships(
                text, entity_names, entity_variations
            )
        )

        # Apply dependency parsing for complex relationships
        relationships.extend(self._extract_dependency_relationships(text, entities))

        # Apply co-occurrence analysis
        relationships.extend(self._extract_cooccurrence_relationships(text, entities))

        # Remove duplicates and filter by confidence
        relationships = self._deduplicate_relationships(relationships)

        return relationships

    def _create_entity_variations(self, entities: List[Entity]) -> Dict[str, str]:
        """Create variations of entity names for better matching."""
        variations = {}

        for entity in entities:
            name = entity.name
            name_lower = name.lower()

            # Add exact match
            variations[name_lower] = name

            # Add singular/plural variations
            if name_lower.endswith("s") and len(name_lower) > 3:
                variations[name_lower[:-1]] = name  # Remove 's'
            else:
                variations[name_lower + "s"] = name  # Add 's'

            # Add variations without common words
            words = name_lower.split()
            if len(words) > 1:
                # Try combinations without articles, prepositions
                stop_words = {
                    "the",
                    "a",
                    "an",
                    "of",
                    "in",
                    "on",
                    "at",
                    "to",
                    "for",
                    "with",
                }
                filtered_words = [w for w in words if w not in stop_words]
                if filtered_words:
                    variations[" ".join(filtered_words)] = name
                    # Also try just the main noun (usually last word)
                    variations[filtered_words[-1]] = name

        return variations

    def _extract_direct_relationships(
        self, text: str, entity_names: Dict[str, str], entity_variations: Dict[str, str]
    ) -> List[Relationship]:
        """Extract relationships using direct pattern matching."""
        relationships = []

        for pattern, rel_type in self.relationship_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                groups = match.groups()

                if len(groups) == 2:
                    source, target = groups
                elif len(groups) == 3:
                    # Handle three-group patterns (e.g., "A sends B to C")
                    source, middle, target = groups
                    # Create two relationships
                    relationships.extend(
                        [
                            self._create_relationship_if_valid(
                                source.strip(),
                                middle.strip(),
                                rel_type,
                                entity_variations,
                                0.8,
                            ),
                            self._create_relationship_if_valid(
                                middle.strip(),
                                target.strip(),
                                "sent_to",
                                entity_variations,
                                0.7,
                            ),
                        ]
                    )
                    continue
                else:
                    continue

                relationship = self._create_relationship_if_valid(
                    source.strip(), target.strip(), rel_type, entity_variations, 0.7
                )
                if relationship:
                    relationships.append(relationship)

        return [r for r in relationships if r is not None]

    def _extract_contextual_relationships(
        self, text: str, entity_names: Dict[str, str], entity_variations: Dict[str, str]
    ) -> List[Relationship]:
        """Extract relationships using contextual patterns."""
        relationships = []

        for pattern, rel_type in self.contextual_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                source = match.group(1).strip()
                target = match.group(2).strip()

                relationship = self._create_relationship_if_valid(
                    source, target, rel_type, entity_variations, 0.6
                )
                if relationship:
                    relationships.append(relationship)

        return relationships

    def _extract_dependency_relationships(
        self, text: str, entities: List[Entity]
    ) -> List[Relationship]:
        """Extract relationships using spaCy dependency parsing."""
        relationships = []

        try:
            doc = self.nlp(text)
            entity_spans = {entity.name.lower(): entity for entity in entities}

            for sent in doc.sents:
                # Look for subject-verb-object patterns
                for token in sent:
                    if token.dep_ == "nsubj" and token.head.pos_ == "VERB":
                        subject = token.text.lower()
                        verb = token.head.lemma_.lower()

                        # Find direct objects
                        for child in token.head.children:
                            if child.dep_ == "dobj":
                                obj = child.text.lower()

                                # Map verb to relationship type
                                rel_type = self._map_verb_to_relationship(verb)
                                if (
                                    rel_type
                                    and subject in entity_spans
                                    and obj in entity_spans
                                ):
                                    relationships.append(
                                        Relationship(
                                            source=entity_spans[subject].name,
                                            target=entity_spans[obj].name,
                                            type=rel_type,
                                            label=rel_type.replace("_", " ").title(),
                                            confidence=0.6,
                                        )
                                    )
        except Exception:
            # If dependency parsing fails, continue without it
            pass

        return relationships

    def _extract_cooccurrence_relationships(
        self, text: str, entities: List[Entity]
    ) -> List[Relationship]:
        """Extract relationships based on entity co-occurrence in sentences."""
        relationships = []

        try:
            doc = self.nlp(text)

            for sent in doc.sents:
                sent_text = sent.text.lower()
                # Find entities that appear in the same sentence
                entities_in_sent = [
                    entity for entity in entities if entity.name.lower() in sent_text
                ]

                # Create weak association relationships for co-occurring entities
                if len(entities_in_sent) >= 2:
                    for i, entity1 in enumerate(entities_in_sent):
                        for entity2 in entities_in_sent[i + 1 :]:
                            # Only create weak associations if no stronger relationship exists
                            relationships.append(
                                Relationship(
                                    source=entity1.name,
                                    target=entity2.name,
                                    type="associated_with",
                                    label="Associated With",
                                    confidence=0.3,
                                )
                            )
        except Exception:
            pass

        return relationships

    def _create_relationship_if_valid(
        self,
        source: str,
        target: str,
        rel_type: str,
        entity_variations: Dict[str, str],
        confidence: float,
    ) -> Optional[Relationship]:
        """Create a relationship if both source and target are valid entities."""
        source_key = source.lower()
        target_key = target.lower()

        # Try exact match first
        source_entity = entity_variations.get(source_key)
        target_entity = entity_variations.get(target_key)

        # Try fuzzy matching if exact match fails
        if not source_entity:
            source_entity = self._fuzzy_match_entity(source_key, entity_variations)
        if not target_entity:
            target_entity = self._fuzzy_match_entity(target_key, entity_variations)

        if source_entity and target_entity and source_entity != target_entity:
            return Relationship(
                source=source_entity,
                target=target_entity,
                type=rel_type,
                label=rel_type.replace("_", " ").title(),
                confidence=confidence,
            )

        return None

    def _fuzzy_match_entity(
        self, text: str, entity_variations: Dict[str, str]
    ) -> Optional[str]:
        """Attempt fuzzy matching for entity names."""
        # Simple fuzzy matching - check if text is contained in any entity name
        for entity_key, entity_name in entity_variations.items():
            if text in entity_key or entity_key in text:
                if abs(len(text) - len(entity_key)) <= 2:  # Allow small differences
                    return entity_name
        return None

    def _map_verb_to_relationship(self, verb: str) -> Optional[str]:
        """Map verbs to relationship types."""
        verb_mapping = {
            "create": "creates",
            "make": "creates",
            "generate": "creates",
            "produce": "creates",
            "use": "uses",
            "utilize": "uses",
            "employ": "uses",
            "send": "sends",
            "transmit": "sends",
            "receive": "receives",
            "get": "receives",
            "contain": "contains",
            "include": "contains",
            "have": "contains",
            "manage": "manages",
            "control": "manages",
            "process": "processes",
            "handle": "processes",
            "store": "stores",
            "save": "stores",
            "validate": "validates",
            "verify": "validates",
            "trigger": "triggers",
            "initiate": "triggers",
            "depend": "depends_on",
            "require": "depends_on",
            "need": "depends_on",
        }
        return verb_mapping.get(verb)

    def _deduplicate_relationships(
        self, relationships: List[Relationship]
    ) -> List[Relationship]:
        """Remove duplicate relationships and keep the one with highest confidence."""
        seen = {}

        for rel in relationships:
            key = (rel.source, rel.target, rel.type)
            reverse_key = (rel.target, rel.source, rel.type)

            # Check for exact match
            if key in seen:
                if rel.confidence > seen[key].confidence:
                    seen[key] = rel
            # Check for reverse relationship (for symmetric relationships)
            elif reverse_key in seen and rel.type in [
                "associated_with",
                "communicates_with",
            ]:
                if rel.confidence > seen[reverse_key].confidence:
                    seen[reverse_key] = rel
            else:
                seen[key] = rel

        # Filter out low-confidence relationships if higher-confidence ones exist
        filtered_relationships = []
        for rel in seen.values():
            # Only include weak associations if no stronger relationships exist between entities
            if rel.type == "associated_with" and rel.confidence < 0.5:
                stronger_exists = any(
                    r.source == rel.source
                    and r.target == rel.target
                    and r.confidence > 0.5
                    for r in seen.values()
                    if r != rel
                )
                if not stronger_exists:
                    filtered_relationships.append(rel)
            else:
                filtered_relationships.append(rel)

        return filtered_relationships

    def determine_diagram_type(
        self, text: str, entities: List[Entity], relationships: List[Relationship]
    ) -> DiagramType:
        """
        Determine the most appropriate diagram type using advanced content analysis.

        Args:
            text: Original text
            entities: Extracted entities
            relationships: Extracted relationships

        Returns:
            Suggested diagram type with confidence scoring
        """
        # Calculate scores for each diagram type
        scores = {
            DiagramType.ERD: self._calculate_erd_score(text, entities, relationships),
            DiagramType.SEQUENCE: self._calculate_sequence_score(
                text, entities, relationships
            ),
            DiagramType.CLASS: self._calculate_class_score(
                text, entities, relationships
            ),
            DiagramType.PROCESS: self._calculate_process_score(
                text, entities, relationships
            ),
            DiagramType.FLOWCHART: self._calculate_flowchart_score(
                text, entities, relationships
            ),
        }

        # Return the diagram type with the highest score
        best_type = max(scores.items(), key=lambda x: x[1])

        # If no type has a strong score, default to flowchart
        if best_type[1] < 0.3:
            return DiagramType.FLOWCHART

        return best_type[0]

    def _calculate_erd_score(
        self, text: str, entities: List[Entity], relationships: List[Relationship]
    ) -> float:
        """Calculate score for Entity Relationship Diagram."""
        score = 0.0
        text_lower = text.lower()

        # Keyword indicators
        erd_keywords = [
            "database",
            "table",
            "schema",
            "entity",
            "attribute",
            "primary key",
            "foreign key",
            "relationship",
            "one-to-many",
            "many-to-many",
            "one-to-one",
            "normalization",
            "sql",
            "record",
            "field",
            "column",
            "row",
            "index",
            "constraint",
            "relational",
        ]

        keyword_matches = sum(1 for keyword in erd_keywords if keyword in text_lower)
        score += keyword_matches * 0.15

        # Entity type analysis
        entity_type_counts = {}
        for entity in entities:
            entity_type_counts[entity.type] = entity_type_counts.get(entity.type, 0) + 1

        # High number of DATA entities suggests ERD
        data_entities = entity_type_counts.get(EntityType.DATA, 0)
        if data_entities > 2:
            score += 0.4
        elif data_entities > 0:
            score += 0.2

        # Object entities that could represent database tables
        object_entities = entity_type_counts.get(EntityType.OBJECT, 0)
        if object_entities > 1:
            score += 0.2

        # Relationship analysis
        erd_relationship_types = [
            "contains",
            "belongs_to",
            "associated_with",
            "references",
        ]
        erd_relationships = [
            r for r in relationships if r.type in erd_relationship_types
        ]
        if len(erd_relationships) > 0:
            score += len(erd_relationships) * 0.1

        # Structural indicators
        if len(entities) > 3 and len(relationships) > 2:
            score += 0.2

        return min(score, 1.0)

    def _calculate_sequence_score(
        self, text: str, entities: List[Entity], relationships: List[Relationship]
    ) -> float:
        """Calculate score for Sequence Diagram."""
        score = 0.0
        text_lower = text.lower()

        # Keyword indicators
        sequence_keywords = [
            "sequence",
            "interaction",
            "message",
            "timeline",
            "communication",
            "request",
            "response",
            "call",
            "invoke",
            "send",
            "receive",
            "actor",
            "participant",
            "lifeline",
            "activation",
            "synchronous",
            "asynchronous",
            "return",
            "reply",
            "step",
            "order",
            "flow",
        ]

        keyword_matches = sum(
            1 for keyword in sequence_keywords if keyword in text_lower
        )
        score += keyword_matches * 0.12

        # Entity type analysis
        entity_type_counts = {}
        for entity in entities:
            entity_type_counts[entity.type] = entity_type_counts.get(entity.type, 0) + 1

        # Actors and systems suggest sequence diagrams
        actors = entity_type_counts.get(EntityType.ACTOR, 0)
        systems = entity_type_counts.get(EntityType.SYSTEM, 0)

        if actors > 0 and systems > 0:
            score += 0.3
        elif actors > 0 or systems > 0:
            score += 0.15

        # Relationship analysis
        communication_types = [
            "sends",
            "receives",
            "communicates_with",
            "calls",
            "invokes",
        ]
        comm_relationships = [
            r for r in relationships if any(ct in r.type for ct in communication_types)
        ]
        if len(comm_relationships) > 0:
            score += len(comm_relationships) * 0.15

        # Temporal indicators
        temporal_words = ["after", "before", "then", "next", "first", "finally", "when"]
        temporal_matches = sum(1 for word in temporal_words if word in text_lower)
        score += temporal_matches * 0.08

        return min(score, 1.0)

    def _calculate_class_score(
        self, text: str, entities: List[Entity], relationships: List[Relationship]
    ) -> float:
        """Calculate score for Class Diagram."""
        score = 0.0
        text_lower = text.lower()

        # Keyword indicators
        class_keywords = [
            "class",
            "object",
            "inheritance",
            "extends",
            "inherits",
            "implements",
            "interface",
            "abstract",
            "method",
            "attribute",
            "property",
            "encapsulation",
            "polymorphism",
            "composition",
            "aggregation",
            "association",
            "dependency",
            "generalization",
            "specialization",
            "superclass",
            "subclass",
            "parent",
            "child",
            "derived",
        ]

        keyword_matches = sum(1 for keyword in class_keywords if keyword in text_lower)
        score += keyword_matches * 0.15

        # Entity type analysis - objects are key for class diagrams
        entity_type_counts = {}
        for entity in entities:
            entity_type_counts[entity.type] = entity_type_counts.get(entity.type, 0) + 1

        objects = entity_type_counts.get(EntityType.OBJECT, 0)
        if objects > 2:
            score += 0.4
        elif objects > 0:
            score += 0.2

        # Relationship analysis
        class_relationship_types = [
            "inherits",
            "implements",
            "extends",
            "is_a",
            "composition",
            "aggregation",
        ]
        class_relationships = [
            r for r in relationships if r.type in class_relationship_types
        ]
        if len(class_relationships) > 0:
            score += len(class_relationships) * 0.2

        # Structure indicators
        if len(entities) > 2 and any(
            "class" in entity.name.lower() for entity in entities
        ):
            score += 0.3

        return min(score, 1.0)

    def _calculate_process_score(
        self, text: str, entities: List[Entity], relationships: List[Relationship]
    ) -> float:
        """Calculate score for Process/Workflow Diagram."""
        score = 0.0
        text_lower = text.lower()

        # Keyword indicators
        process_keywords = [
            "process",
            "workflow",
            "procedure",
            "step",
            "task",
            "activity",
            "business process",
            "operation",
            "function",
            "action",
            "execute",
            "perform",
            "complete",
            "start",
            "end",
            "begin",
            "finish",
            "decision",
            "condition",
            "branch",
            "loop",
            "iteration",
            "approval",
            "review",
            "validation",
            "verification",
        ]

        keyword_matches = sum(
            1 for keyword in process_keywords if keyword in text_lower
        )
        score += keyword_matches * 0.12

        # Entity type analysis
        entity_type_counts = {}
        for entity in entities:
            entity_type_counts[entity.type] = entity_type_counts.get(entity.type, 0) + 1

        # Process entities are key indicators
        processes = entity_type_counts.get(EntityType.PROCESS, 0)
        if processes > 2:
            score += 0.5
        elif processes > 0:
            score += 0.3

        # Events also suggest process diagrams
        events = entity_type_counts.get(EntityType.EVENT, 0)
        if events > 0:
            score += events * 0.15

        # Relationship analysis
        process_relationship_types = [
            "triggers",
            "follows",
            "precedes",
            "leads_to",
            "causes",
        ]
        process_relationships = [
            r for r in relationships if r.type in process_relationship_types
        ]
        if len(process_relationships) > 0:
            score += len(process_relationships) * 0.15

        # Sequential indicators
        sequential_words = [
            "step",
            "phase",
            "stage",
            "first",
            "second",
            "third",
            "next",
            "then",
            "finally",
        ]
        sequential_matches = sum(1 for word in sequential_words if word in text_lower)
        score += sequential_matches * 0.08

        return min(score, 1.0)

    def _calculate_flowchart_score(
        self, text: str, entities: List[Entity], relationships: List[Relationship]
    ) -> float:
        """Calculate score for Flowchart (default/general purpose)."""
        score = 0.3  # Base score as fallback option
        text_lower = text.lower()

        # Keyword indicators
        flowchart_keywords = [
            "flow",
            "chart",
            "diagram",
            "logic",
            "algorithm",
            "decision",
            "condition",
            "if",
            "else",
            "loop",
            "while",
            "for",
            "branch",
            "path",
            "route",
            "direction",
            "control flow",
        ]

        keyword_matches = sum(
            1 for keyword in flowchart_keywords if keyword in text_lower
        )
        score += keyword_matches * 0.1

        # General relationship indicators
        flow_relationship_types = ["flows_to", "leads_to", "goes_to", "proceeds_to"]
        flow_relationships = [
            r for r in relationships if r.type in flow_relationship_types
        ]
        if len(flow_relationships) > 0:
            score += len(flow_relationships) * 0.1

        # Mixed entity types suggest general flowchart
        entity_type_counts = {}
        for entity in entities:
            entity_type_counts[entity.type] = entity_type_counts.get(entity.type, 0) + 1

        unique_types = len(entity_type_counts)
        if unique_types > 2:
            score += 0.2

        # Decision-making indicators
        decision_words = [
            "if",
            "when",
            "unless",
            "decide",
            "choose",
            "select",
            "determine",
        ]
        decision_matches = sum(1 for word in decision_words if word in text_lower)
        score += decision_matches * 0.05

        return min(score, 1.0)

    def get_diagram_type_suggestions(
        self, text: str, entities: List[Entity], relationships: List[Relationship]
    ) -> Dict[str, float]:
        """
        Get all diagram type suggestions with their confidence scores.

        Args:
            text: Original text
            entities: Extracted entities
            relationships: Extracted relationships

        Returns:
            Dictionary mapping diagram types to confidence scores
        """
        scores = {
            "erd": self._calculate_erd_score(text, entities, relationships),
            "sequence": self._calculate_sequence_score(text, entities, relationships),
            "class": self._calculate_class_score(text, entities, relationships),
            "process": self._calculate_process_score(text, entities, relationships),
            "flowchart": self._calculate_flowchart_score(text, entities, relationships),
        }

        # Sort by confidence score
        return dict(sorted(scores.items(), key=lambda x: x[1], reverse=True))

    def _classify_entity_type(
        self, entity_name: str, spacy_label: str = None
    ) -> EntityType:
        """
        Classify entity type based on name and context.

        Args:
            entity_name: Name of the entity
            spacy_label: spaCy entity label if available

        Returns:
            Classified entity type
        """
        name_lower = entity_name.lower()

        # Check spaCy labels first
        if spacy_label:
            if spacy_label == "PERSON":
                return EntityType.ACTOR
            elif spacy_label == "ORG":
                return EntityType.SYSTEM
            elif spacy_label == "EVENT":
                return EntityType.EVENT

        # Check against keyword sets
        if any(keyword in name_lower for keyword in self.process_keywords):
            return EntityType.PROCESS
        elif any(keyword in name_lower for keyword in self.system_keywords):
            return EntityType.SYSTEM
        elif any(keyword in name_lower for keyword in self.data_keywords):
            return EntityType.DATA
        elif (
            "user" in name_lower
            or "admin" in name_lower
            or "customer" in name_lower
            or "client" in name_lower
        ):
            return EntityType.ACTOR

        # Default classification
        return EntityType.OBJECT

    def _calculate_confidence(
        self, entities: List[Entity], relationships: List[Relationship]
    ) -> float:
        """
        Calculate overall confidence score for the parsing results.

        Args:
            entities: List of extracted entities
            relationships: List of extracted relationships

        Returns:
            Confidence score between 0 and 1
        """
        if not entities:
            return 0.0

        # Average entity confidence
        entity_confidence = sum(entity.confidence for entity in entities) / len(
            entities
        )

        # Relationship confidence (bonus for having relationships)
        relationship_bonus = min(len(relationships) * 0.1, 0.3)

        # Combine scores
        total_confidence = min(entity_confidence + relationship_bonus, 1.0)

        return round(total_confidence, 2)
