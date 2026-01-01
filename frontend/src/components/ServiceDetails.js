import React, { useState, useEffect } from 'react';

const ServiceDetails = () => {
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(true);
  const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  useEffect(() => {
    const fetchServices = async () => {
      try {
        const response = await fetch(`${apiUrl}/api/services`);
        const data = await response.json();
        
        // FIX: Convert object to array
        const servicesArray = data.services 
          ? Object.values(data.services)
          : [];
        
        setServices(servicesArray);
      } catch (error) {
        console.error('Failed to fetch services:', error);
        setServices([]);
      } finally {
        setLoading(false);
      }
    };

    fetchServices();
  }, [apiUrl]);

  if (loading) {
    return <div className="sidebar-section">Loading services...</div>;
  }

  if (services.length === 0) {
    return <div className="sidebar-section">No services available</div>;
  }

  return (
    <div className="sidebar-section">
      <h3>Available Services</h3>
      <div className="services-list">
        {services.slice(0, 5).map((service) => (
          <div key={service.id} className="service-item">
            <h4>{service.name}</h4>
            <p className="service-price">€{service.price_eur}</p>
            <p className="service-duration">{service.duration_minutes} min</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ServiceDetails;
