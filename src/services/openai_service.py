"""
OpenAI GPT-4 integration service
Handles content generation and prompt engineering
"""
import openai
from openai import OpenAI
import logging
import time
from typing import Dict, List, Optional, Tuple
import json
import re
from dataclasses import dataclass

@dataclass
class GenerationResult:
    """Content generation result"""
    content: str
    tokens_used: int
    response_time: float
    model: str
    finish_reason: str

class PromptTemplates:
    """Collection of prompt templates for different use cases"""
    
    RAG_CONTENT_GENERATION = """
You are an expert content generator. Based on the provided context and user query, create high-quality, informative content.

Context Information:
{context}

User Query: {query}

Instructions:
1. Use the provided context to inform your response
2. Create comprehensive, well-structured content
3. Maintain factual accuracy based on the context
4. Write in a clear, engaging style
5. Include relevant details from the context
6. If the context is insufficient, indicate what additional information would be helpful

Content:
"""

    SUMMARIZATION = """
Summarize the following content in a clear, concise manner while preserving key information:

Content: {content}

Summary:
"""

    QUESTION_ANSWERING = """
Answer the following question based on the provided context. Be accurate and comprehensive.

Context: {context}

Question: {query}

Answer:
"""

    CONTENT_EXPANSION = """
Expand the following content with additional details, examples, and insights:

Original Content: {content}

Additional Context: {context}

Expanded Content:
"""

    CREATIVE_WRITING = """
Create engaging, creative content based on the following prompt and context:

Context: {context}

Creative Prompt: {query}

Creative Content:
"""

class OpenAIService:
    """OpenAI API service for content generation"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.api_key = config.get('OPENAI_API_KEY')
        self.model = config.get('OPENAI_MODEL', 'gpt-4-turbo-preview')
        self.max_tokens = config.get('OPENAI_MAX_TOKENS', 2000)
        self.temperature = config.get('OPENAI_TEMPERATURE', 0.7)
        self.timeout = config.get('REQUEST_TIMEOUT', 30)
        
        self.logger = logging.getLogger(__name__)
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        # Initialize OpenAI client with timeout settings
        self.client = OpenAI(
            api_key=self.api_key,
            timeout=120.0,  # Increase timeout to 2 minutes
            max_retries=3   # Add retry logic
        )
        
        # Initialize prompt templates
        self.templates = PromptTemplates()
        
        # Track usage statistics
        self.usage_stats = {
            'total_requests': 0,
            'total_tokens': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0.0
        }
    
    def generate_content(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        model: Optional[str] = None
    ) -> GenerationResult:
        """Generate content using OpenAI API with retry logic"""
        start_time = time.time()
        
        # Use defaults if not specified
        max_tokens = max_tokens or self.max_tokens
        temperature = temperature or self.temperature
        model = model or self.model
        
        # Retry logic with exponential backoff
        max_retries = 3
        base_delay = 1
        
        for attempt in range(max_retries):
            try:
                self.logger.debug(f"Generating content with model: {model} (attempt {attempt + 1})")
                
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
                response_time = time.time() - start_time
                
                # Extract response data
                content = response.choices[0].message.content
                tokens_used = response.usage.total_tokens
                finish_reason = response.choices[0].finish_reason
                
                # Update statistics
                self._update_stats(response_time, tokens_used, True)
                
                result = GenerationResult(
                    content=content,
                    tokens_used=tokens_used,
                    response_time=response_time,
                    model=model,
                    finish_reason=finish_reason
                )
                
                self.logger.info(f"Content generated successfully. Tokens: {tokens_used}, Time: {response_time:.2f}s")
                return result
                
            except Exception as e:
                self.logger.warning(f"Generation attempt {attempt + 1} failed: {str(e)}")
                
                if attempt == max_retries - 1:  # Last attempt
                    response_time = time.time() - start_time
                    self._update_stats(response_time, 0, False)
                    self.logger.error(f"Content generation failed after {max_retries} attempts: {str(e)}")
                    raise
                
                # Exponential backoff delay
                delay = base_delay * (2 ** attempt)
                self.logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
    
    def generate_with_context(
        self,
        query: str,
        context: str,
        template_type: str = 'rag',
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> GenerationResult:
        """Generate content with context using predefined templates"""
        
        # Select appropriate template
        if template_type == 'rag':
            template = self.templates.RAG_CONTENT_GENERATION
        elif template_type == 'qa':
            template = self.templates.QUESTION_ANSWERING
        elif template_type == 'summary':
            template = self.templates.SUMMARIZATION
        elif template_type == 'expand':
            template = self.templates.CONTENT_EXPANSION
        elif template_type == 'creative':
            template = self.templates.CREATIVE_WRITING
        else:
            template = self.templates.RAG_CONTENT_GENERATION
        
        # Format prompt with context and query
        if template_type == 'summary':
            formatted_prompt = template.format(content=context)
        else:
            formatted_prompt = template.format(context=context, query=query)
        
        return self.generate_content(
            prompt=formatted_prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
    
    def generate_streaming(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        model: Optional[str] = None
    ):
        """Generate content with streaming response"""
        max_tokens = max_tokens or self.max_tokens
        temperature = temperature or self.temperature
        model = model or self.model
        
        try:
            self.logger.debug(f"Starting streaming generation with model: {model}")
            
            stream = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
                timeout=self.timeout
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            self.logger.error(f"Streaming generation failed: {str(e)}")
            raise
    
    def batch_generate(
        self,
        prompts: List[str],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        model: Optional[str] = None
    ) -> List[GenerationResult]:
        """Generate content for multiple prompts"""
        results = []
        
        for i, prompt in enumerate(prompts):
            try:
                self.logger.debug(f"Processing batch item {i+1}/{len(prompts)}")
                result = self.generate_content(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    model=model
                )
                results.append(result)
                
                # Add small delay to avoid rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Batch generation failed for item {i+1}: {str(e)}")
                # Add placeholder result for failed generation
                results.append(GenerationResult(
                    content=f"Generation failed: {str(e)}",
                    tokens_used=0,
                    response_time=0.0,
                    model=model or self.model,
                    finish_reason="error"
                ))
        
        return results
    
    def improve_content(self, content: str, instructions: str) -> GenerationResult:
        """Improve existing content based on instructions"""
        prompt = f"""
Improve the following content based on these instructions: {instructions}

Original Content:
{content}

Improved Content:
"""
        return self.generate_content(prompt)
    
    def extract_keywords(self, content: str) -> List[str]:
        """Extract keywords from content"""
        prompt = f"""
Extract the most important keywords and phrases from the following content. 
Return them as a comma-separated list.

Content:
{content}

Keywords:
"""
        result = self.generate_content(prompt, max_tokens=200, temperature=0.3)
        
        # Parse keywords from response
        keywords_text = result.content.strip()
        keywords = [k.strip() for k in keywords_text.split(',')]
        return [k for k in keywords if k]  # Remove empty strings
    
    def generate_title(self, content: str) -> str:
        """Generate a title for content"""
        prompt = f"""
Generate a compelling, informative title for the following content:

Content:
{content[:500]}...

Title:
"""
        result = self.generate_content(prompt, max_tokens=50, temperature=0.5)
        return result.content.strip().strip('"').strip("'")
    
    def check_content_quality(self, content: str) -> Dict:
        """Analyze content quality and provide feedback"""
        prompt = f"""
Analyze the following content and provide feedback on:
1. Clarity and readability
2. Information completeness
3. Structure and organization
4. Overall quality score (1-10)

Format your response as JSON with keys: clarity, completeness, structure, overall_score, suggestions

Content:
{content}

Analysis:
"""
        
        result = self.generate_content(prompt, max_tokens=500, temperature=0.3)
        
        try:
            # Try to parse JSON response
            quality_data = json.loads(result.content)
            return quality_data
        except json.JSONDecodeError:
            # Fallback to text analysis
            return {
                'clarity': 'Unable to parse',
                'completeness': 'Unable to parse',
                'structure': 'Unable to parse',
                'overall_score': 0,
                'suggestions': result.content
            }
    
    def _update_stats(self, response_time: float, tokens: int, success: bool):
        """Update usage statistics"""
        self.usage_stats['total_requests'] += 1
        self.usage_stats['total_tokens'] += tokens
        
        if success:
            self.usage_stats['successful_requests'] += 1
        else:
            self.usage_stats['failed_requests'] += 1
        
        # Update average response time
        total_requests = self.usage_stats['total_requests']
        current_avg = self.usage_stats['average_response_time']
        self.usage_stats['average_response_time'] = (
            (current_avg * (total_requests - 1) + response_time) / total_requests
        )
    
    def get_usage_stats(self) -> Dict:
        """Get usage statistics"""
        return self.usage_stats.copy()
    
    def reset_stats(self):
        """Reset usage statistics"""
        self.usage_stats = {
            'total_requests': 0,
            'total_tokens': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0.0
        }
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough approximation)"""
        # Rough estimation: 1 token ≈ 4 characters for English
        return len(text) // 4
    
    def validate_api_key(self) -> bool:
        """Validate OpenAI API key"""
        try:
            # Try a minimal API call
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return True
        except Exception as e:
            self.logger.error(f"API key validation failed: {str(e)}")
            return False

# Example usage
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Example configuration
    config = {
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'OPENAI_MODEL': 'gpt-4-turbo-preview',
        'OPENAI_MAX_TOKENS': 1000,
        'OPENAI_TEMPERATURE': 0.7,
        'REQUEST_TIMEOUT': 30
    }
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize OpenAI service
    openai_service = OpenAIService(config)
    
    # Test content generation
    if openai_service.validate_api_key():
        # Example with context
        context = "Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience."
        query = "Explain machine learning for beginners"
        
        result = openai_service.generate_with_context(
            query=query,
            context=context,
            template_type='rag'
        )
        
        print(f"Generated content: {result.content}")
        print(f"Tokens used: {result.tokens_used}")
        print(f"Response time: {result.response_time:.2f}s")
        
        # Get usage stats
        stats = openai_service.get_usage_stats()
        print(f"Usage stats: {stats}")
    else:
        print("Invalid API key or service unavailable")