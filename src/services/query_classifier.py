"""
Query Classification Service
Determines whether a query needs RAG research or can be answered conversationally
"""
import logging
import re
from typing import Dict, List, Tuple
from enum import Enum

class QueryType(Enum):
    CONVERSATIONAL = "conversational"  # Simple greetings, thanks, etc.
    FACTUAL = "factual"               # Needs research/RAG
    MIXED = "mixed"                   # May need light research

class QueryClassifier:
    """Classifies queries to determine appropriate response strategy"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Conversational patterns that don't need RAG
        self.conversational_patterns = [
            # Greetings
            r'\b(hello|hi|hey|greetings|good morning|good afternoon|good evening)\b',
            r'\b(how are you|how\'s it going|what\'s up)\b',
            
            # Thanks and politeness
            r'\b(thank you|thanks|thank you very much|appreciate it)\b',
            r'\b(please|excuse me|sorry|pardon)\b',
            
            # Goodbyes
            r'\b(goodbye|bye|see you|farewell|take care)\b',
            
            # Simple responses
            r'\b(yes|no|ok|okay|sure|alright)\b',
            r'\b(i see|i understand|got it|makes sense)\b',
            
            # Personal/subjective questions
            r'\b(what do you think|your opinion|how do you feel)\b',
            r'\b(can you help|what can you do|what are your capabilities)\b',
        ]
        
        # Keywords that suggest factual queries needing RAG
        self.factual_keywords = [
            # Question words for factual information
            'what is', 'what are', 'what was', 'what were',
            'how does', 'how do', 'how did', 'how to',
            'why does', 'why do', 'why did', 'why is',
            'when did', 'when was', 'when will', 'when does',
            'where is', 'where are', 'where was', 'where can',
            'who is', 'who was', 'who are', 'which is',
            
            # Information seeking terms
            'explain', 'describe', 'tell me about', 'information about',
            'details about', 'facts about', 'definition of',
            'meaning of', 'examples of', 'list of',
            
            # Current/recent information
            'latest', 'recent', 'current', 'today', 'now',
            'news', 'updates', 'developments', 'trends',
            
            # Technical/academic terms
            'research', 'study', 'analysis', 'theory',
            'science', 'technology', 'medicine', 'physics',
            'chemistry', 'biology', 'mathematics', 'engineering',
            'computer', 'software', 'artificial intelligence',
            'machine learning', 'quantum', 'blockchain',
        ]
        
        # Compile regex patterns
        self.conversational_regex = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.conversational_patterns
        ]
    
    def classify_query(self, query: str) -> Tuple[QueryType, float, str]:
        """
        Classify a query and return type, confidence, and reasoning
        
        Args:
            query: User's query text
            
        Returns:
            Tuple of (QueryType, confidence_score, reasoning)
        """
        query_lower = query.lower().strip()
        
        # Handle very short queries
        if len(query_lower) <= 2:
            return QueryType.CONVERSATIONAL, 0.9, "Very short query, likely conversational"
        
        # Check for conversational patterns
        conversational_matches = []
        for pattern in self.conversational_regex:
            if pattern.search(query_lower):
                conversational_matches.append(pattern.pattern)
        
        # Check for factual keywords
        factual_matches = []
        for keyword in self.factual_keywords:
            if keyword in query_lower:
                factual_matches.append(keyword)
        
        # Determine classification
        if conversational_matches and not factual_matches:
            confidence = min(0.95, 0.7 + 0.1 * len(conversational_matches))
            reasoning = f"Matched conversational patterns: {conversational_matches[:2]}"
            return QueryType.CONVERSATIONAL, confidence, reasoning
        
        elif factual_matches and not conversational_matches:
            confidence = min(0.95, 0.7 + 0.05 * len(factual_matches))
            reasoning = f"Matched factual keywords: {factual_matches[:3]}"
            return QueryType.FACTUAL, confidence, reasoning
        
        elif factual_matches and conversational_matches:
            # Mixed query - lean towards factual if strong indicators
            if len(factual_matches) > len(conversational_matches):
                confidence = 0.6
                reasoning = f"Mixed query with more factual indicators: {factual_matches[:2]}"
                return QueryType.FACTUAL, confidence, reasoning
            else:
                confidence = 0.6
                reasoning = f"Mixed query with more conversational indicators: {conversational_matches[:2]}"
                return QueryType.CONVERSATIONAL, confidence, reasoning
        
        else:
            # No clear indicators - use query length and structure as heuristics
            word_count = len(query_lower.split())
            
            if word_count <= 3 and not any(char in query_lower for char in '?'):
                # Short statements without questions are likely conversational
                return QueryType.CONVERSATIONAL, 0.6, "Short statement, likely conversational"
            
            elif '?' in query and word_count > 3:
                # Questions with substance are likely factual
                return QueryType.FACTUAL, 0.6, "Question format with substance, likely factual"
            
            else:
                # Default to conversational for unclear cases
                return QueryType.CONVERSATIONAL, 0.5, "Unclear query, defaulting to conversational"
    
    def should_use_rag(self, query: str, confidence_threshold: float = 0.7) -> Tuple[bool, str]:
        """
        Determine if RAG should be used for a query
        
        Args:
            query: User's query
            confidence_threshold: Minimum confidence for classification
            
        Returns:
            Tuple of (should_use_rag, reasoning)
        """
        query_type, confidence, reasoning = self.classify_query(query)
        
        # Use RAG for factual queries with high confidence
        if query_type == QueryType.FACTUAL and confidence >= confidence_threshold:
            return True, f"Factual query (confidence: {confidence:.2f}) - {reasoning}"
        
        # Don't use RAG for conversational queries with high confidence
        elif query_type == QueryType.CONVERSATIONAL and confidence >= confidence_threshold:
            return False, f"Conversational query (confidence: {confidence:.2f}) - {reasoning}"
        
        # For low confidence or mixed queries, use a conservative approach
        else:
            # Default to RAG for ambiguous cases, but with simpler search
            return True, f"Ambiguous query (confidence: {confidence:.2f}) - Using RAG with simplified search"
    
    def get_conversational_response(self, query: str) -> str:
        """Generate appropriate conversational responses"""
        query_lower = query.lower().strip()
        
        # Greetings
        if any(word in query_lower for word in ['hello', 'hi', 'hey', 'greetings']):
            return "Hello! I'm your RAG-powered AI assistant. I can help answer questions by searching through real-time web data and my knowledge base. What would you like to know?"
        
        # Good morning/afternoon/evening
        elif 'good morning' in query_lower:
            return "Good morning! How can I assist you today?"
        elif 'good afternoon' in query_lower:
            return "Good afternoon! What can I help you with?"
        elif 'good evening' in query_lower:
            return "Good evening! How may I help you?"
        
        # How are you
        elif any(phrase in query_lower for phrase in ['how are you', 'how\'s it going', 'what\'s up']):
            return "I'm doing well, thank you for asking! I'm ready to help you with any questions or information you need. What would you like to explore?"
        
        # Thanks
        elif any(word in query_lower for word in ['thank', 'thanks', 'appreciate']):
            return "You're very welcome! Is there anything else I can help you with?"
        
        # Goodbyes
        elif any(word in query_lower for word in ['goodbye', 'bye', 'farewell']):
            return "Goodbye! Feel free to come back anytime if you have more questions. Have a great day!"
        
        # Capabilities
        elif any(phrase in query_lower for phrase in ['what can you do', 'your capabilities', 'can you help']):
            return "I'm a RAG-powered AI assistant that can help you with a wide range of questions! I can:\n\n• Search the web for current information\n• Access my knowledge base for established facts\n• Provide detailed explanations with source citations\n• Help with research, learning, and problem-solving\n\nWhat topic would you like to explore?"
        
        # Simple acknowledgments
        elif any(word in query_lower for word in ['yes', 'ok', 'okay', 'sure', 'alright']):
            return "Great! What would you like to know more about?"
        
        # Default conversational response
        else:
            return "I understand. Is there something specific you'd like to know about? I can search for current information and provide detailed answers with sources."