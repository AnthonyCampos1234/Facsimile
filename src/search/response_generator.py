from typing import List, Dict, Optional
from langchain.prompts import PromptTemplate
from loguru import logger
from langchain.schema import Document

class ResponseGenerator:
    """Generates contextual responses from search results"""
    
    def __init__(self, llm):
        self.llm = llm
        self.templates = self._create_templates()
        
    def _create_templates(self) -> Dict[str, PromptTemplate]:
        """Create different templates for different types of responses"""
        return {
            "general": PromptTemplate(
                input_variables=["summaries", "messages", "identity", "query"],
                template="""
                Using the following information, answer the user's query.
                
                Weekly Summaries: {summaries}
                
                Recent Messages: {messages}
                
                Identity Context: {identity}
                
                User Query: {query}
                
                Provide a clear, concise answer that combines high-level insights with specific details when relevant.
                Format the response to clearly distinguish between summary information and specific message quotes.
                """
            ),
            "time_specific": PromptTemplate(
                input_variables=["time_period", "messages", "query"],
                template="""
                Answer the user's query about this specific time period: {time_period}
                
                Relevant Messages: {messages}
                
                Query: {query}
                
                Provide specific details from the messages while maintaining context.
                """
            )
        }
    
    def generate_response(self, 
                         query: str,
                         search_results: Dict,
                         response_type: str = "general") -> str:
        """Generate a response based on search results"""
        try:
            template = self.templates.get(response_type, self.templates["general"])
            
            # Format inputs based on response type
            if response_type == "time_specific":
                inputs = {
                    "time_period": f"{search_results.get('start_date', 'Unknown')} to {search_results.get('end_date', 'Unknown')}",
                    "messages": self._format_messages(search_results.get("messages", [])),
                    "query": query
                }
            else:
                inputs = {
                    "summaries": self._format_summaries(search_results.get("summaries", [])),
                    "messages": self._format_messages(search_results.get("messages", [])),
                    "identity": self._format_identity(search_results.get("identity", [])),
                    "query": query
                }
            
            # Create and invoke chain using the new pipe syntax
            chain = template | self.llm
            response = chain.invoke(inputs)
            
            # Handle different response types
            if hasattr(response, 'content'):
                return response.content
            elif isinstance(response, str):
                return response
            else:
                return str(response)
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I apologize, but I encountered an error generating a response."
    
    def _format_summaries(self, summaries: List[Document]) -> str:
        """Format weekly summaries for the prompt"""
        formatted = []
        for summary in summaries:
            formatted.append(
                f"Time Period: {summary.metadata.get('week_start', 'Unknown')} to {summary.metadata.get('week_end', 'Unknown')}\n"
                f"Contact: {summary.metadata.get('contact', 'Unknown')}\n"
                f"Summary: {summary.page_content}\n"
            )
        return "\n".join(formatted)
    
    def _format_messages(self, messages: List[Document]) -> str:
        """Format individual messages for the prompt"""
        formatted = []
        for msg in messages:
            formatted.append(
                f"[{msg.metadata.get('timestamp', 'Unknown')}] "
                f"{msg.metadata.get('sender', 'Unknown')}: {msg.page_content}"
            )
        return "\n".join(formatted)
    
    def _format_identity(self, identity: List[Document]) -> str:
        """Format identity information for the prompt"""
        if not identity:
            return "No identity information available."
        
        formatted = []
        for info in identity:
            formatted.append(
                f"Contact: {info.metadata.get('contact', 'Unknown')}\n"
                f"Relationship Context: {info.page_content}"
            )
        return "\n".join(formatted) 