"""CrewAI Agents for Medical Clinic System."""
from crewai import Agent
from langchain_community.llms import Ollama
from typing import List
import os


class MedicalAgents:
    """Factory class for creating specialized medical agents."""

    def __init__(self, tools: List = None):
        """Initialize agents with tools.
        
        Args:
            tools: List of tools available to agents
        """
        self.tools = tools or []
        self.llm = self._create_llm()

    def _create_llm(self):
        """Create Ollama LLM instance."""
        return Ollama(
            model="gemma2:2b",
            base_url="http://localhost:11434",
            temperature=0.7
        )

    def reception_agent(self) -> Agent:
        """Create the Reception Agent (Anna).
        
        Welcomes patients, understands initial concerns,
        and provides warm, professional first contact.
        """
        return Agent(
            role="Medical Clinic Receptionist",
            goal="Warmly welcome patients, understand their initial concerns, "
                 "and guide them through the clinic's services professionally",
            backstory="You are Anna, an experienced medical receptionist with 10 years "
                     "of experience. You're known for your warm, empathetic approach and "
                     "ability to make patients feel comfortable. You have excellent "
                     "communication skills and always maintain a professional yet friendly "
                     "demeanor. You're the first point of contact for patients and set "
                     "the tone for their entire experience at MedCare Clinic.",
            tools=self.tools,
            llm=self.llm,
            verbose=True,
            allow_delegation=True,
            memory=True
        )

    def symptoms_analyzer_agent(self) -> Agent:
        """Create the Symptoms Analyzer Agent (Dr. Med).
        
        Analyzes patient symptoms and recommends appropriate
        medical services.
        """
        return Agent(
            role="Medical Symptoms Analyzer",
            goal="Carefully analyze patient symptoms, understand their medical concerns, "
                 "and recommend the most appropriate medical services from the clinic's offerings",
            backstory="You are Dr. Med, a medical triage specialist with expertise in "
                     "symptom analysis and service matching. You have 15 years of experience "
                     "in emergency medicine and patient intake. You're skilled at asking the "
                     "right questions to understand patient conditions and matching them to "
                     "appropriate specialists and services. You always prioritize patient "
                     "safety and ensure urgent cases are identified quickly. You explain "
                     "medical services in simple, understandable terms.",
            tools=self.tools,
            llm=self.llm,
            verbose=True,
            allow_delegation=True,
            memory=True
        )

    def booking_manager_agent(self) -> Agent:
        """Create the Booking Manager Agent (Registry).
        
        Manages appointment slots, extracts patient details,
        and confirms bookings.
        """
        return Agent(
            role="Appointment Booking Manager",
            goal="Efficiently manage appointment scheduling, collect accurate patient "
                 "information, check availability, and confirm bookings with all necessary details",
            backstory="You are Registry, an expert appointment coordinator with exceptional "
                     "organizational skills. You've managed clinic schedules for 12 years and "
                     "have a perfect track record of zero double-bookings. You're detail-oriented, "
                     "precise, and always confirm information with patients to avoid errors. "
                     "You understand the importance of collecting accurate patient information "
                     "(full name, date of birth) and always verify appointment details before "
                     "finalizing bookings. You provide clear, structured confirmation summaries.",
            tools=self.tools,
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            memory=True
        )

    def get_all_agents(self) -> List[Agent]:
        """Get all agents as a list.
        
        Returns:
            List of all medical agents
        """
        return [
            self.reception_agent(),
            self.symptoms_analyzer_agent(),
            self.booking_manager_agent()
        ]
