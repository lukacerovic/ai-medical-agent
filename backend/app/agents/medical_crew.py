"""Medical Crew Orchestrator - Main CrewAI Workflow Manager"""

from crewai import Crew, Process
from typing import Dict, Any, List, Optional
import json
import os
from datetime import datetime
from enum import Enum

from .crew_config import CrewConfig
from .medical_agents import MedicalAgents
from .medical_tasks import MedicalTasks

class ConversationState(Enum):
    """States in the medical consultation workflow."""
    GREETING = "greeting"
    SYMPTOMS = "symptoms"
    SERVICE_SELECTION = "service_selection"
    BOOKING = "booking"
    CONFIRMATION = "confirmation"
    COMPLETED = "completed"

class MedicalCrew:
    """
    Main orchestrator for the medical agent crew.
    Manages conversation flow, state transitions, and agent coordination.
    """
    
    def __init__(self, session_id: str, config: Optional[CrewConfig] = None):
        """
        Initialize medical crew for a patient session.
        
        Args:
            session_id: Unique identifier for this patient session
            config: CrewAI configuration
        """
        self.session_id = session_id
        self.config = config or CrewConfig()
        
        # Initialize agents and tasks
        self.agents_factory = MedicalAgents(self.config)
        self.tasks_factory = MedicalTasks(self.config)
        
        # Create all agents
        self.agents = self.agents_factory.create_all_agents()
        
        # Session state
        self.conversation_state = ConversationState.GREETING
        self.conversation_history: List[Dict[str, str]] = []
        self.extracted_info: Dict[str, Any] = {}
        self.selected_service: Optional[Dict[str, Any]] = None
        
        # Load data
        self.services_data = self._load_services()
        self.availability_data = self._load_availability()
    
    def _load_services(self) -> List[Dict[str, Any]]:
        """Load available medical services."""
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        services_file = os.path.join(data_dir, 'services.json')
        
        try:
            with open(services_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
    
    def _load_availability(self) -> Dict[str, Any]:
        """Load appointment availability."""
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        availability_file = os.path.join(data_dir, 'availability.json')
        
        try:
            with open(availability_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def _determine_next_state(self, patient_message: str) -> ConversationState:
        """
        Determine next conversation state based on message and history.
        
        Args:
            patient_message: Patient's message
            
        Returns:
            Next conversation state
        """
        message_lower = patient_message.lower()
        
        # State transition logic
        if self.conversation_state == ConversationState.GREETING:
            # First message - check if symptoms mentioned
            symptom_keywords = ["pain", "hurt", "problem", "issue", "sick", "feel"]
            if any(keyword in message_lower for keyword in symptom_keywords):
                return ConversationState.SYMPTOMS
            return ConversationState.GREETING
        
        elif self.conversation_state == ConversationState.SYMPTOMS:
            # After symptoms - check if ready to book
            booking_keywords = ["yes", "book", "appointment", "schedule", "when"]
            if any(keyword in message_lower for keyword in booking_keywords):
                return ConversationState.BOOKING
            return ConversationState.SERVICE_SELECTION
        
        elif self.conversation_state == ConversationState.SERVICE_SELECTION:
            # Service selected - move to booking
            return ConversationState.BOOKING
        
        elif self.conversation_state == ConversationState.BOOKING:
            # Check if all info collected
            if self._has_all_booking_info():
                return ConversationState.CONFIRMATION
            return ConversationState.BOOKING
        
        elif self.conversation_state == ConversationState.CONFIRMATION:
            return ConversationState.COMPLETED
        
        return self.conversation_state
    
    def _has_all_booking_info(self) -> bool:
        """Check if all required booking information is collected."""
        required_fields = ["patient_name", "dob", "date", "time"]
        return all(field in self.extracted_info for field in required_fields)
    
    def process_message(self, patient_message: str) -> Dict[str, Any]:
        """
        Process patient message through the crew.
        
        Args:
            patient_message: Patient's message
            
        Returns:
            Response with AI reply and updated state
        """
        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": patient_message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Determine next state
        new_state = self._determine_next_state(patient_message)
        self.conversation_state = new_state
        
        # Prepare context
        context = {
            "history": self.conversation_history,
            "services": self.services_data,
            "availability": self.availability_data,
            "selected_service": self.selected_service,
            "extracted_info": self.extracted_info,
        }
        
        # Create tasks for current state
        tasks = self.tasks_factory.create_conversation_tasks(
            agents=self.agents,
            patient_message=patient_message,
            conversation_state=self.conversation_state.value,
            context=context
        )
        
        if not tasks:
            return self._generate_default_response(patient_message)
        
        # Create and execute crew
        crew = Crew(
            agents=list(self.agents.values()),
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
            memory=True,
        )
        
        try:
            # Execute crew
            result = crew.kickoff()
            
            # Extract response
            if hasattr(result, 'raw'):
                response_text = result.raw
            else:
                response_text = str(result)
            
            # Add to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": response_text,
                "timestamp": datetime.now().isoformat()
            })
            
            # Return structured response
            return {
                "response": response_text,
                "state": self.conversation_state.value,
                "extracted_info": self.extracted_info,
                "selected_service": self.selected_service,
                "conversation_history": self.conversation_history,
            }
        
        except Exception as e:
            error_message = f"I apologize, but I encountered an issue processing your request. Could you please try again? Error: {str(e)}"
            
            self.conversation_history.append({
                "role": "assistant",
                "content": error_message,
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "response": error_message,
                "state": self.conversation_state.value,
                "error": str(e),
                "conversation_history": self.conversation_history,
            }
    
    def _generate_default_response(self, patient_message: str) -> Dict[str, Any]:
        """Generate a default response when no tasks are created."""
        response = (
            "Thank you for your message. I'm here to help you schedule "
            "an appointment at MedCare Clinic. Could you please tell me "
            "what brings you in today?"
        )
        
        self.conversation_history.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "response": response,
            "state": self.conversation_state.value,
            "conversation_history": self.conversation_history,
        }
    
    def get_session_state(self) -> Dict[str, Any]:
        """
        Get current session state.
        
        Returns:
            Complete session state
        """
        return {
            "session_id": self.session_id,
            "state": self.conversation_state.value,
            "conversation_history": self.conversation_history,
            "extracted_info": self.extracted_info,
            "selected_service": self.selected_service,
        }
    
    def reset_session(self):
        """Reset session to initial state."""
        self.conversation_state = ConversationState.GREETING
        self.conversation_history = []
        self.extracted_info = {}
        self.selected_service = None
