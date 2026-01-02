"""CrewAI Configuration for Medical Agent System"""

from crewai import Agent, Crew, Task, Process
from crewai_tools import BaseTool
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import os

class CrewConfig:
    """
    Configuration manager for CrewAI medical agent system.
    Handles agent definitions, task configurations, and crew orchestration.
    """
    
    def __init__(self, llm_config: Optional[Dict[str, Any]] = None):
        """
        Initialize CrewAI configuration.
        
        Args:
            llm_config: Configuration for LLM (e.g., Ollama settings)
        """
        self.llm_config = llm_config or self._get_default_llm_config()
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        
    def _get_default_llm_config(self) -> Dict[str, Any]:
        """Get default LLM configuration for Ollama."""
        return {
            "model": "gemma2:2b",
            "base_url": "http://localhost:11434",
            "temperature": 0.7,
        }
    
    def get_reception_agent_config(self) -> Dict[str, Any]:
        """
        Configuration for Reception Agent (Anna).
        
        Role: First point of contact, welcomes patients warmly,
        understands initial concerns, routes to appropriate services.
        """
        return {
            "role": "Medical Clinic Receptionist",
            "goal": "Welcome patients warmly and understand their medical needs to provide excellent first-contact experience",
            "backstory": (
                "You are Anna, a friendly and professional medical clinic receptionist "
                "with 10 years of experience in patient care. You excel at making patients "
                "feel comfortable and understood. You have excellent communication skills "
                "and can quickly identify patient needs to route them to the right services. "
                "You always maintain a warm, empathetic tone while being professional."
            ),
            "verbose": True,
            "allow_delegation": True,
            "memory": True,
        }
    
    def get_symptoms_analyzer_config(self) -> Dict[str, Any]:
        """
        Configuration for Symptoms Analyzer Agent (Dr. Med).
        
        Role: Analyzes patient symptoms, recommends appropriate services,
        provides medical context and education.
        """
        return {
            "role": "Medical Symptoms Analyzer",
            "goal": "Analyze patient symptoms accurately and recommend the most appropriate medical services",
            "backstory": (
                "You are Dr. Med, an experienced medical triage specialist with extensive "
                "knowledge of various medical conditions and symptoms. You have worked in "
                "emergency departments and primary care for 15 years, developing excellent "
                "diagnostic intuition. You can match patient symptoms to appropriate medical "
                "services while explaining the reasoning in simple, patient-friendly language. "
                "You prioritize patient safety and always consider severity of symptoms."
            ),
            "verbose": True,
            "allow_delegation": False,
            "memory": True,
        }
    
    def get_booking_manager_config(self) -> Dict[str, Any]:
        """
        Configuration for Booking Manager Agent (Registry).
        
        Role: Manages appointment slots, extracts patient details,
        confirms bookings, updates availability.
        """
        return {
            "role": "Appointment Booking Specialist",
            "goal": "Efficiently manage appointment scheduling and ensure accurate patient information collection",
            "backstory": (
                "You are Registry, a highly organized and detail-oriented appointment "
                "coordinator with 8 years of experience in medical scheduling systems. "
                "You are expert at managing complex calendars, extracting accurate patient "
                "information, and preventing double-bookings. You have a systematic approach "
                "to data collection and always verify important details before confirmation. "
                "You're patient and thorough when collecting sensitive information."
            ),
            "verbose": True,
            "allow_delegation": False,
            "memory": True,
        }
    
    def get_task_configs(self) -> Dict[str, Any]:
        """
        Get configurations for all tasks in the medical workflow.
        """
        return {
            "patient_greeting": {
                "description": (
                    "Greet the patient warmly and professionally. Introduce yourself as Anna "
                    "from MedCare Clinic. Ask how you can help them today. Listen carefully "
                    "to their initial concern and acknowledge their feelings with empathy. "
                    "Patient message: {patient_message}"
                ),
                "expected_output": (
                    "A warm, professional greeting that acknowledges the patient's concern "
                    "and makes them feel comfortable. Should include: clinic name, your name, "
                    "acknowledgment of their issue, and a clear indication you're ready to help."
                ),
            },
            "symptom_analysis": {
                "description": (
                    "Analyze the patient's symptoms and medical concerns described in: {patient_message}. "
                    "Consider the conversation history: {conversation_history}. "
                    "Based on available services in {services_data}, identify which service(s) "
                    "would be most appropriate. Explain why this service matches their needs "
                    "in simple, patient-friendly language. Consider symptom severity and urgency."
                ),
                "expected_output": (
                    "A clear medical service recommendation with: 1) The matched service name, "
                    "2) Brief explanation of why it's appropriate for their symptoms, "
                    "3) Service details (price, duration), 4) Any relevant health information "
                    "the patient should know."
                ),
            },
            "appointment_booking": {
                "description": (
                    "Manage the appointment booking process for the patient. "
                    "Service selected: {selected_service}. "
                    "Current conversation: {conversation_history}. "
                    "Available slots: {availability_data}. "
                    "\n\nTasks:\n"
                    "1. Show available appointment slots in a clear format\n"
                    "2. Extract patient's preferred date and time from their response\n"
                    "3. Collect patient personal information: full name and date of birth\n"
                    "4. Validate all collected information before confirmation\n"
                    "5. Create booking confirmation with all details\n"
                    "6. Provide clear next steps (arrival time, what to bring, etc.)"
                ),
                "expected_output": (
                    "Complete booking confirmation including: Patient name, Date of birth, "
                    "Service name, Appointment date and time, Price, Duration, Booking ID, "
                    "and arrival instructions. All information must be accurate and verified."
                ),
            },
            "conversation_routing": {
                "description": (
                    "Analyze the patient's message: {patient_message} and conversation history: {conversation_history}. "
                    "Determine the appropriate next step: \n"
                    "- If new patient/greeting: route to reception\n"
                    "- If discussing symptoms: route to symptom analyzer\n"
                    "- If ready to book/selecting time: route to booking manager\n"
                    "- If asking questions about service: provide clear answers\n"
                    "- If booking complete: provide confirmation and next steps"
                ),
                "expected_output": (
                    "Clear routing decision with explanation, next agent to handle request, "
                    "and any context that should be passed to the next agent."
                ),
            },
        }
    
    def get_crew_config(self) -> Dict[str, Any]:
        """
        Configuration for the overall crew behavior.
        """
        return {
            "process": Process.sequential,  # Tasks executed in order
            "verbose": True,
            "memory": True,  # Enable conversation memory
            "max_rpm": 10,  # Rate limiting
            "share_crew": False,
        }
