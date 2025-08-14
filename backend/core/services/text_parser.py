"""
Text parsing service for extracting 
entities and relationships from unstructured text.
"""
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List

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
            'create', 'generate', 'process', 'handle', 'manage', 'execute',
            'run', 'start', 'stop', 'finish', 'complete', 'validate',
            'authenticate', 'authorize', 'send', 'receive', 'update',
            'delete', 'save', 'load', 'transform', 'convert'
        }
        
        # System-related keywords
        self.system_keywords = {
            'system', 'service', 'api', 'database', 'server', 'client',
            'application', 'platform', 'interface', 'module', 'component'
        }
        
        # Data-related keywords
        self.data_keywords = {
            'data', 'information', 'record', 'file', 'document', 'report',
            'message', 'request', 'response', 'payload', 'schema'
        }
        
        # Relationship indicators
        self.relationship_patterns = [
            (r'\b(\w+)\s+(?:creates?|generates?)\s+(\w+)', 'creates'),
            (r'\b(\w+)\s+(?:uses?|utilizes?)\s+(\w+)', 'uses'),
            (r'\b(\w+)\s+(?:sends?|transmits?)\s+(\w+)', 'sends'),
            (r'\b(\w+)\s+(?:receives?|gets?)\s+(\w+)', 'receives'),
            (r'\b(\w+)\s+(?:contains?|includes?)\s+(\w+)', 'contains'),
            (r'\b(\w+)\s+(?:depends?\s+on|requires?)\s+(\w+)', 'depends_on'),
            (r'\b(\w+)\s+(?:inherits?\s+from|extends?)\s+(\w+)', 'inherits'),
            (r'\b(\w+)\s+(?:flows?\s+to|goes?\s+to)\s+(\w+)', 'flows_to'),
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
                confidence=0.0,
                raw_text=text
            )
        
        # Process text with spaCy
        doc = self.nlp(text)
        
        # Extract entities
        entities = self.extract_entities(doc)
        
        # Extract relationships
        relationships = self.identify_relationships(text, entities)
        
        # Determine diagram type
        diagram_type = self.determine_diagram_type(text, entities, relationships)
        
        # Calculate overall confidence
        confidence = self._calculate_confidence(entities, relationships)
        
        return ParsedContent(
            entities=entities,
            relationships=relationships,
            suggested_diagram_type=diagram_type,
            confidence=confidence,
            raw_text=text
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
            if ent.label_ in ['PERSON', 'ORG', 'PRODUCT', 'EVENT']:
                entity_name = ent.text.strip()
                if entity_name and entity_name.lower() not in processed_entities:
                    entity_type = self._classify_entity_type(entity_name, ent.label_)
                    entities.append(Entity(
                        name=entity_name,
                        type=entity_type,
                        properties={'spacy_label': ent.label_},
                        confidence=0.8,
                        start_pos=ent.start_char,
                        end_pos=ent.end_char
                    ))
                    processed_entities.add(entity_name.lower())
        
        # Extract noun phrases as potential entities
        for chunk in doc.noun_chunks:
            entity_name = chunk.text.strip()
            if (entity_name and 
                len(entity_name.split()) <= 3 and  # Limit to reasonable length
                entity_name.lower() not in processed_entities and
                not any(token.is_stop for token in chunk if not token.is_alpha)):
                
                entity_type = self._classify_entity_type(entity_name)
                entities.append(Entity(
                    name=entity_name,
                    type=entity_type,
                    properties={'source': 'noun_phrase'},
                    confidence=0.6,
                    start_pos=chunk.start_char,
                    end_pos=chunk.end_char
                ))
                processed_entities.add(entity_name.lower())
        
        return entities
    
    def identify_relationships(self, text: str, entities: List[Entity]) -> List[Relationship]:
        """
        Identify relationships between entities using pattern matching.
        
        Args:
            text: Original text
            entities: List of extracted entities
            
        Returns:
            List of identified relationships
        """
        relationships = []
        entity_names = {entity.name.lower(): entity.name for entity in entities}
        
        # Apply relationship patterns
        for pattern, rel_type in self.relationship_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                source = match.group(1).strip()
                target = match.group(2).strip()
                
                # Check if both source and target are recognized entities
                source_key = source.lower()
                target_key = target.lower()
                
                if source_key in entity_names and target_key in entity_names:
                    relationships.append(Relationship(
                        source=entity_names[source_key],
                        target=entity_names[target_key],
                        type=rel_type,
                        label=rel_type.replace('_', ' ').title(),
                        confidence=0.7
                    ))
        
        return relationships
    
    def determine_diagram_type(self, text: str, entities: List[Entity], 
                             relationships: List[Relationship]) -> DiagramType:
        """
        Determine the most appropriate diagram type based on content analysis.
        
        Args:
            text: Original text
            entities: Extracted entities
            relationships: Extracted relationships
            
        Returns:
            Suggested diagram type
        """
        text_lower = text.lower()
        
        # Count different types of entities
        entity_type_counts = {}
        for entity in entities:
            entity_type_counts[entity.type] = entity_type_counts.get(entity.type, 0) + 1
        
        # Count relationship types
        relationship_types = [rel.type for rel in relationships]
        
        # Decision logic for diagram type
        
        # ERD indicators
        if ('database' in text_lower or 'table' in text_lower or 
            'schema' in text_lower or 'entity' in text_lower or
            entity_type_counts.get(EntityType.DATA, 0) > 2):
            return DiagramType.ERD
        
        # Sequence diagram indicators
        if ('sequence' in text_lower or 'interaction' in text_lower or
            'message' in text_lower or 'timeline' in text_lower or
            any(rel_type in ['sends', 'receives'] for rel_type in relationship_types)):
            return DiagramType.SEQUENCE
        
        # Class diagram indicators
        if ('class' in text_lower or 'inheritance' in text_lower or
            'extends' in text_lower or 'inherits' in text_lower or
            any(rel_type == 'inherits' for rel_type in relationship_types)):
            return DiagramType.CLASS
        
        # Process diagram indicators
        if ('process' in text_lower or 'workflow' in text_lower or
            'procedure' in text_lower or 'steps' in text_lower or
            entity_type_counts.get(EntityType.PROCESS, 0) > 1):
            return DiagramType.PROCESS
        
        # Default to flowchart
        return DiagramType.FLOWCHART
    
    def _classify_entity_type(self, entity_name: str, spacy_label: str = None) -> EntityType:
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
            if spacy_label == 'PERSON':
                return EntityType.ACTOR
            elif spacy_label == 'ORG':
                return EntityType.SYSTEM
            elif spacy_label == 'EVENT':
                return EntityType.EVENT
        
        # Check against keyword sets
        if any(keyword in name_lower for keyword in self.process_keywords):
            return EntityType.PROCESS
        elif any(keyword in name_lower for keyword in self.system_keywords):
            return EntityType.SYSTEM
        elif any(keyword in name_lower for keyword in self.data_keywords):
            return EntityType.DATA
        elif ('user' in name_lower or 'admin' in name_lower or 
              'customer' in name_lower or 'client' in name_lower):
            return EntityType.ACTOR
        
        # Default classification
        return EntityType.OBJECT
    
    def _calculate_confidence(self, entities: List[Entity], 
                            relationships: List[Relationship]) -> float:
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
        entity_confidence = sum(entity.confidence for entity in entities) / len(entities)
        
        # Relationship confidence (bonus for having relationships)
        relationship_bonus = min(len(relationships) * 0.1, 0.3)
        
        # Combine scores
        total_confidence = min(entity_confidence + relationship_bonus, 1.0)
        
        return round(total_confidence, 2)