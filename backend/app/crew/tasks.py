"""CrewAI Tasks for Medical Clinic Workflow."""
from crewai import Task
from typing import List
from .agents import MedicalAgents


class MedicalTasks:
    """Factory class for creating medical clinic tasks."""

    def __init__(self, agents: MedicalAgents):
        """Initialize tasks with agents.
        
        Args:
            agents: MedicalAgents instance containing all agents
        """
        self.agents = agents

    def reception_task(self, patient_message: str, conversation_history: List[dict]) -> Task:
        """Create reception greeting and initial assessment task.
        
        Args:
            patient_message: Current message from patient
            conversation_history: Previous messages in conversation
            
        Returns:
            Task for reception agent
        """
        history_text = self._format_history(conversation_history)
        
        return Task(
            description=f"""Welcome the patient and provide initial assistance.
            
            Patient's Current Message: {patient_message}
            
            Conversation History:
            {history_text}
            
            Your responsibilities:
            1. Greet the patient warmly (if first message)
            2. Acknowledge their concerns with empathy
            3. Ask clarifying questions about their symptoms if needed
            4. Maintain a professional yet friendly tone
            5. Prepare to delegate to symptoms analyzer if medical assessment is needed
            
            If patient mentions symptoms or medical concerns, acknowledge and prepare
            for specialist analysis. If they ask about services, pricing, or availability,
            provide general information and offer to connect them with the right specialist.
            """,
            agent=self.agents.reception_agent(),
            expected_output="A warm, professional response that acknowledges the patient's "
                          "concerns and either answers their question or indicates next steps"
        )

    def symptoms_analysis_task(self, patient_message: str, conversation_history: List[dict]) -> Task:
        """Create symptoms analysis and service matching task.
        
        Args:
            patient_message: Current message from patient
            conversation_history: Previous messages in conversation
            
        Returns:
            Task for symptoms analyzer agent
        """
        history_text = self._format_history(conversation_history)
        
        return Task(
            description=f"""Analyze patient symptoms and recommend appropriate medical services.
            
            Patient's Current Message: {patient_message}
            
            Conversation History:
            {history_text}
            
            Your responsibilities:
            1. Carefully review the patient's symptoms and concerns
            2. Ask follow-up questions if needed to understand the condition better
            3. Use the service_lookup tool to find matching services
            4. Recommend the most appropriate service(s) based on symptoms
            5. Explain why the service is suitable in simple terms
            6. Provide service details (name, price, duration, description)
            7. Assess if this is urgent/emergency (if yes, recommend immediate action)
            
            Available Services to Consider:
            - Cardiology Consultation (€120, 45min) - for heart-related issues
            - Gastroenterology Consultation (€110, 40min) - for digestive issues
            - Blood Analysis (€50, 20min) - for general health screening
            - Dermatology Consultation (€100, 30min) - for skin conditions
            - General Practice (€80, 30min) - for general health concerns
            
            Provide clear, empathetic medical guidance.
            """,
            agent=self.agents.symptoms_analyzer_agent(),
            expected_output="A detailed analysis of symptoms with specific service recommendations, "
                          "including service names, prices, durations, and clear explanations of why "
                          "each service is appropriate for the patient's condition"
        )

    def booking_task(self, patient_message: str, conversation_history: List[dict], 
                     service_id: str = None) -> Task:
        """Create appointment booking task.
        
        Args:
            patient_message: Current message from patient
            conversation_history: Previous messages in conversation
            service_id: ID of service to book (if known)
            
        Returns:
            Task for booking manager agent
        """
        history_text = self._format_history(conversation_history)
        service_context = f"Service to book: {service_id}" if service_id else "Service needs to be determined"
        
        return Task(
            description=f"""Manage the appointment booking process for the patient.
            
            Patient's Current Message: {patient_message}
            
            Conversation History:
            {history_text}
            
            {service_context}
            
            Your responsibilities:
            1. Check if service has been selected (if not, ask patient to choose)
            2. Use check_availability tool to show available time slots
            3. Collect patient information:
               - Full name (first and last name)
               - Date of birth (format: YYYY-MM-DD)
            4. Confirm the selected date and time
            5. Verify all details with the patient before finalizing
            6. Use create_booking tool to finalize the appointment
            7. Provide a clear confirmation summary with all details
            
            Booking Checklist:
            □ Service selected
            □ Date and time chosen
            □ Patient full name collected
            □ Date of birth collected
            □ All details confirmed
            □ Booking created
            
            Always double-check information accuracy. Ask for confirmation before
            creating the booking.
            """,
            agent=self.agents.booking_manager_agent(),
            expected_output="A complete booking confirmation with all details: patient name, "
                          "date of birth, service name, appointment date and time, price, "
                          "duration, and booking ID. Include instructions for the patient "
                          "(e.g., arrive 10 minutes early)"
        )

    def information_query_task(self, patient_message: str, conversation_history: List[dict]) -> Task:
        """Create task for handling general information queries.
        
        Args:
            patient_message: Current message from patient
            conversation_history: Previous messages in conversation
            
        Returns:
            Task for reception agent
        """
        history_text = self._format_history(conversation_history)
        
        return Task(
            description=f"""Answer the patient's general inquiry about clinic services.
            
            Patient's Current Message: {patient_message}
            
            Conversation History:
            {history_text}
            
            Common queries to handle:
            - Clinic hours and location
            - General pricing information
            - Services overview
            - Insurance and payment options
            - How to prepare for appointments
            - Follow-up procedures
            
            Provide clear, helpful information. If the query requires booking or
            symptom analysis, guide the patient to the appropriate next step.
            """,
            agent=self.agents.reception_agent(),
            expected_output="A clear, informative response that addresses the patient's "
                          "question and provides any relevant additional context"
        )

    def _format_history(self, conversation_history: List[dict]) -> str:
        """Format conversation history for task descriptions.
        
        Args:
            conversation_history: List of message dictionaries
            
        Returns:
            Formatted conversation string
        """
        if not conversation_history:
            return "(No previous conversation)"
        
        formatted = []
        for msg in conversation_history[-10:]:
            role = "Patient" if msg.get("role") == "user" else "Assistant"
            content = msg.get("content", "")
            formatted.append(f"{role}: {content}")
        
        return "\n".join(formatted)

    def get_task_by_intent(self, intent: str, patient_message: str, 
                           conversation_history: List[dict], **kwargs) -> Task:
        """Get appropriate task based on detected intent.
        
        Args:
            intent: Detected user intent
            patient_message: Current patient message
            conversation_history: Previous messages
            **kwargs: Additional parameters (e.g., service_id)
            
        Returns:
            Appropriate Task based on intent
        """
        intent_mapping = {
            "greeting": self.reception_task,
            "symptoms": self.symptoms_analysis_task,
            "book_appointment": self.booking_task,
            "service_inquiry": self.symptoms_analysis_task,
            "information": self.information_query_task,
        }
        
        task_creator = intent_mapping.get(intent, self.reception_task)
        
        if intent == "book_appointment" and "service_id" in kwargs:
            return task_creator(patient_message, conversation_history, kwargs["service_id"])
        
        return task_creator(patient_message, conversation_history)
