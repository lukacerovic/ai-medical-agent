"""CrewAI Crew Orchestration for Medical Clinic."""
from crewai import Crew, Process
from typing import Dict, List, Any
from .agents import MedicalAgents
from .tasks import MedicalTasks
from .tools import get_medical_tools
import logging

logger = logging.getLogger(__name__)


class MedicalClinicCrew:
    """Orchestrates multi-agent workflow for medical clinic operations."""

    def __init__(self):
        """Initialize the medical clinic crew."""
        self.tools = get_medical_tools()
        self.agents = MedicalAgents(tools=self.tools)
        self.tasks_factory = MedicalTasks(self.agents)
        self.conversation_memory = {}

    def detect_intent(self, message: str, history: List[dict]) -> str:
        """Detect user intent from message.
        
        Args:
            message: User message
            history: Conversation history
            
        Returns:
            Intent string
        """
        message_lower = message.lower()
        
        # Intent detection rules
        if not history or len(history) < 2:
            if any(word in message_lower for word in ["hi", "hello", "hey", "good morning"]):
                return "greeting"
        
        if any(word in message_lower for word in ["symptom", "pain", "hurt", "sick", "feel", 
                                                    "problem", "issue", "heart", "stomach", 
                                                    "head", "chest", "dizzy"]):
            return "symptoms"
        
        if any(word in message_lower for word in ["book", "appointment", "schedule", 
                                                    "available", "slot", "when can"]):
            return "book_appointment"
        
        if any(word in message_lower for word in ["service", "offer", "what do you", 
                                                    "treatment", "consultation"]):
            return "service_inquiry"
        
        if any(word in message_lower for word in ["price", "cost", "how much", "location", 
                                                    "hours", "insurance"]):
            return "information"
        
        # Check conversation context
        if history:
            last_response = history[-1].get("content", "").lower()
            if "book" in last_response or "appointment" in last_response:
                return "book_appointment"
            if "service" in last_response or "recommend" in last_response:
                return "symptoms"
        
        return "greeting"

    def process_conversation(self, session_id: str, message: str) -> Dict[str, Any]:
        """Process a conversation turn with multi-agent system.
        
        Args:
            session_id: Unique session identifier
            message: User message
            
        Returns:
            Response dictionary with agent output and metadata
        """
        try:
            # Initialize session memory if needed
            if session_id not in self.conversation_memory:
                self.conversation_memory[session_id] = {
                    "messages": [],
                    "extracted_info": {},
                    "current_intent": None,
                    "booking_state": "not_started"
                }
            
            session = self.conversation_memory[session_id]
            
            # Add user message to history
            session["messages"].append({
                "role": "user",
                "content": message
            })
            
            # Detect intent
            intent = self.detect_intent(message, session["messages"])
            session["current_intent"] = intent
            
            logger.info(f"Session {session_id}: Detected intent '{intent}'")
            
            # Get appropriate task based on intent
            task = self.tasks_factory.get_task_by_intent(
                intent=intent,
                patient_message=message,
                conversation_history=session["messages"],
                service_id=session["extracted_info"].get("service_id")
            )
            
            # Determine which agents to use based on intent
            agents = self._get_agents_for_intent(intent)
            
            # Create crew with appropriate agents
            crew = Crew(
                agents=agents,
                tasks=[task],
                process=Process.sequential,
                verbose=True,
                memory=True
            )
            
            # Execute crew
            result = crew.kickoff()
            
            # Extract response text
            response_text = str(result)
            
            # Add assistant response to history
            session["messages"].append({
                "role": "assistant",
                "content": response_text
            })
            
            # Extract structured information from conversation
            self._extract_information(session, message, response_text)
            
            return {
                "success": True,
                "response": response_text,
                "intent": intent,
                "session_state": {
                    "messages_count": len(session["messages"]),
                    "extracted_info": session["extracted_info"],
                    "booking_state": session["booking_state"]
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing conversation: {str(e)}", exc_info=True)
            return {
                "success": False,
                "response": "I apologize, but I encountered an error processing your request. "
                           "Please try again or contact our staff directly.",
                "error": str(e)
            }

    def _get_agents_for_intent(self, intent: str) -> List:
        """Get appropriate agents based on intent.
        
        Args:
            intent: Detected intent
            
        Returns:
            List of agents to use
        """
        if intent in ["greeting", "information"]:
            return [self.agents.reception_agent()]
        elif intent in ["symptoms", "service_inquiry"]:
            return [
                self.agents.reception_agent(),
                self.agents.symptoms_analyzer_agent()
            ]
        elif intent == "book_appointment":
            return [
                self.agents.reception_agent(),
                self.agents.booking_manager_agent()
            ]
        else:
            return [self.agents.reception_agent()]

    def _extract_information(self, session: Dict, message: str, response: str):
        """Extract structured information from conversation.
        
        Args:
            session: Session data
            message: User message
            response: Agent response
        """
        import re
        
        # Extract service ID
        service_patterns = [
            r"cardiology",
            r"gastroenterology",
            r"blood analysis",
            r"dermatology",
            r"general practice"
        ]
        
        combined_text = (message + " " + response).lower()
        
        for pattern in service_patterns:
            if pattern in combined_text:
                service_id = pattern.replace(" ", "_")
                session["extracted_info"]["service_id"] = service_id
                break
        
        # Extract date (YYYY-MM-DD or natural language)
        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", combined_text)
        if date_match:
            session["extracted_info"]["date"] = date_match.group(1)
        
        # Extract time (HH:MM)
        time_match = re.search(r"(\d{1,2}:\d{2})", combined_text)
        if time_match:
            session["extracted_info"]["time"] = time_match.group(1)
        
        # Extract patient name (simple detection)
        name_match = re.search(r"(?:my name is|i'm|i am)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)", message, re.IGNORECASE)
        if name_match:
            session["extracted_info"]["patient_name"] = name_match.group(1)
        
        # Update booking state
        if "service_id" in session["extracted_info"]:
            session["booking_state"] = "service_selected"
        
        if "date" in session["extracted_info"] and "time" in session["extracted_info"]:
            session["booking_state"] = "time_selected"
        
        if "patient_name" in session["extracted_info"]:
            session["booking_state"] = "details_collected"
        
        if "confirmed" in response.lower() or "booking id" in response.lower():
            session["booking_state"] = "completed"

    def get_session_state(self, session_id: str) -> Dict:
        """Get current session state.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session state dictionary
        """
        return self.conversation_memory.get(session_id, {})

    def reset_session(self, session_id: str):
        """Reset session memory.
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.conversation_memory:
            del self.conversation_memory[session_id]
