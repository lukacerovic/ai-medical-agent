"""Medical Task Definitions using CrewAI Framework"""

from crewai import Task
from typing import Dict, Any, List, Optional
from .crew_config import CrewConfig
from .medical_agents import MedicalAgents

class MedicalTasks:
    """
    Factory class for creating medical task instances.
    Tasks define the workflow for patient interaction.
    """
    
    def __init__(self, config: Optional[CrewConfig] = None):
        """
        Initialize medical tasks factory.
        
        Args:
            config: CrewAI configuration object
        """
        self.config = config or CrewConfig()
        self.task_configs = self.config.get_task_configs()
    
    def create_greeting_task(
        self,
        agent,
        patient_message: str,
        conversation_history: List[Dict] = None
    ) -> Task:
        """
        Create task for greeting patient and understanding initial concern.
        
        Args:
            agent: Reception agent to execute this task
            patient_message: Patient's initial message
            conversation_history: Previous conversation messages
            
        Returns:
            Task instance for patient greeting
        """
        config = self.task_configs["patient_greeting"]
        
        return Task(
            description=config["description"].format(
                patient_message=patient_message
            ),
            expected_output=config["expected_output"],
            agent=agent,
            async_execution=False,
        )
    
    def create_symptom_analysis_task(
        self,
        agent,
        patient_message: str,
        conversation_history: List[Dict],
        services_data: List[Dict]
    ) -> Task:
        """
        Create task for analyzing symptoms and matching services.
        
        Args:
            agent: Symptoms analyzer agent
            patient_message: Patient's symptom description
            conversation_history: Previous conversation
            services_data: Available medical services
            
        Returns:
            Task instance for symptom analysis
        """
        config = self.task_configs["symptom_analysis"]
        
        import json
        
        return Task(
            description=config["description"].format(
                patient_message=patient_message,
                conversation_history=json.dumps(conversation_history, indent=2),
                services_data=json.dumps(services_data, indent=2)
            ),
            expected_output=config["expected_output"],
            agent=agent,
            async_execution=False,
        )
    
    def create_booking_task(
        self,
        agent,
        selected_service: Dict[str, Any],
        conversation_history: List[Dict],
        availability_data: Dict[str, Any]
    ) -> Task:
        """
        Create task for managing appointment booking.
        
        Args:
            agent: Booking manager agent
            selected_service: Service patient wants to book
            conversation_history: Previous conversation
            availability_data: Available appointment slots
            
        Returns:
            Task instance for booking management
        """
        config = self.task_configs["appointment_booking"]
        
        import json
        
        return Task(
            description=config["description"].format(
                selected_service=json.dumps(selected_service, indent=2),
                conversation_history=json.dumps(conversation_history, indent=2),
                availability_data=json.dumps(availability_data, indent=2)
            ),
            expected_output=config["expected_output"],
            agent=agent,
            async_execution=False,
        )
    
    def create_routing_task(
        self,
        agent,
        patient_message: str,
        conversation_history: List[Dict]
    ) -> Task:
        """
        Create task for routing patient to appropriate next step.
        
        Args:
            agent: Reception agent
            patient_message: Patient's current message
            conversation_history: Previous conversation
            
        Returns:
            Task instance for conversation routing
        """
        config = self.task_configs["conversation_routing"]
        
        import json
        
        return Task(
            description=config["description"].format(
                patient_message=patient_message,
                conversation_history=json.dumps(conversation_history, indent=2)
            ),
            expected_output=config["expected_output"],
            agent=agent,
            async_execution=False,
        )
    
    def create_conversation_tasks(
        self,
        agents: Dict[str, Any],
        patient_message: str,
        conversation_state: str,
        context: Dict[str, Any]
    ) -> List[Task]:
        """
        Create appropriate tasks based on conversation state.
        
        Args:
            agents: Dictionary of available agents
            patient_message: Patient's message
            conversation_state: Current state (greeting, symptoms, booking, etc.)
            context: Additional context (history, services, availability)
            
        Returns:
            List of tasks to execute
        """
        tasks = []
        
        if conversation_state == "greeting":
            tasks.append(
                self.create_greeting_task(
                    agent=agents["reception"],
                    patient_message=patient_message,
                    conversation_history=context.get("history", [])
                )
            )
        
        elif conversation_state == "symptoms":
            tasks.append(
                self.create_symptom_analysis_task(
                    agent=agents["symptoms_analyzer"],
                    patient_message=patient_message,
                    conversation_history=context.get("history", []),
                    services_data=context.get("services", [])
                )
            )
        
        elif conversation_state == "booking":
            tasks.append(
                self.create_booking_task(
                    agent=agents["booking_manager"],
                    selected_service=context.get("selected_service", {}),
                    conversation_history=context.get("history", []),
                    availability_data=context.get("availability", {})
                )
            )
        
        else:
            # Default routing task
            tasks.append(
                self.create_routing_task(
                    agent=agents["reception"],
                    patient_message=patient_message,
                    conversation_history=context.get("history", [])
                )
            )
        
        return tasks
