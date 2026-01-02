"""Medical Agent Definitions using CrewAI Framework"""

from crewai import Agent
from langchain_ollama import ChatOllama
from typing import List, Optional
from .crew_config import CrewConfig
from .medical_tools import (
    ServiceMatchingTool,
    AvailabilityCheckerTool,
    BookingCreatorTool,
    PatientInfoExtractorTool,
)

class MedicalAgents:
    """
    Factory class for creating medical agent instances.
    Each agent has specific tools and capabilities for their role.
    """
    
    def __init__(self, config: Optional[CrewConfig] = None):
        """
        Initialize medical agents factory.
        
        Args:
            config: CrewAI configuration object
        """
        self.config = config or CrewConfig()
        self.llm = self._create_llm()
        self.tools = self._initialize_tools()
    
    def _create_llm(self) -> ChatOllama:
        """Create LLM instance for agents."""
        return ChatOllama(
            model=self.config.llm_config["model"],
            base_url=self.config.llm_config["base_url"],
            temperature=self.config.llm_config["temperature"],
        )
    
    def _initialize_tools(self) -> dict:
        """Initialize all available tools for agents."""
        return {
            "service_matching": ServiceMatchingTool(),
            "availability_checker": AvailabilityCheckerTool(),
            "booking_creator": BookingCreatorTool(),
            "patient_info_extractor": PatientInfoExtractorTool(),
        }
    
    def create_reception_agent(self) -> Agent:
        """
        Create Reception Agent (Anna).
        
        Responsibilities:
        - Greet patients warmly
        - Understand initial concerns
        - Provide general information
        - Route to appropriate specialist
        
        Tools: Patient info extraction
        """
        config = self.config.get_reception_agent_config()
        
        return Agent(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            verbose=config["verbose"],
            allow_delegation=config["allow_delegation"],
            memory=config["memory"],
            llm=self.llm,
            tools=[self.tools["patient_info_extractor"]],
        )
    
    def create_symptoms_analyzer_agent(self) -> Agent:
        """
        Create Symptoms Analyzer Agent (Dr. Med).
        
        Responsibilities:
        - Analyze patient symptoms
        - Match symptoms to services
        - Provide medical context
        - Assess urgency
        
        Tools: Service matching
        """
        config = self.config.get_symptoms_analyzer_config()
        
        return Agent(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            verbose=config["verbose"],
            allow_delegation=config["allow_delegation"],
            memory=config["memory"],
            llm=self.llm,
            tools=[self.tools["service_matching"]],
        )
    
    def create_booking_manager_agent(self) -> Agent:
        """
        Create Booking Manager Agent (Registry).
        
        Responsibilities:
        - Check appointment availability
        - Extract booking details
        - Create and confirm bookings
        - Update availability
        
        Tools: Availability checker, booking creator, patient info extractor
        """
        config = self.config.get_booking_manager_config()
        
        return Agent(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            verbose=config["verbose"],
            allow_delegation=config["allow_delegation"],
            memory=config["memory"],
            llm=self.llm,
            tools=[
                self.tools["availability_checker"],
                self.tools["booking_creator"],
                self.tools["patient_info_extractor"],
            ],
        )
    
    def create_all_agents(self) -> dict:
        """
        Create all medical agents.
        
        Returns:
            Dictionary with agent names as keys and Agent instances as values
        """
        return {
            "reception": self.create_reception_agent(),
            "symptoms_analyzer": self.create_symptoms_analyzer_agent(),
            "booking_manager": self.create_booking_manager_agent(),
        }
