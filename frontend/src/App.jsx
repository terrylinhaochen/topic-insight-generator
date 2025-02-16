import React, { useState } from 'react';

const DOMAIN_CONFIGS = {
  career: {
    title: "Career Insight Podcast",
    placeholder: "Share a workplace challenge...",
    headerColor: "#1a1a1a"
  },
  parenting: {
    title: "Parenting Insight Podcast",
    placeholder: "Share a parenting challenge...",
    headerColor: "#2a4365"
  }
};

const App = ({ domain = 'career' }) => {
  const [topic, setTopic] = useState('');
  const [insight, setInsight] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [mastodonUrl, setMastodonUrl] = useState(null);

  const config = DOMAIN_CONFIGS[domain];

  const generateInsight = async () => {
    setLoading(true);
    setError(null);
    setMastodonUrl(null);
    
    try {
      const response = await fetch(`http://localhost:8000/api/generate/${domain}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          content: topic
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to generate insight');
      }

      if (!data.content || !data.content[0] || !data.content[0].text) {
        throw new Error('Invalid response format from server');
      }
      
      try {
        const text = data.content[0].text.trim();
        const jsonMatch = text.match(/\{[\s\S]*\}/);
        if (!jsonMatch) {
          throw new Error('No JSON object found in response');
        }
        const parsedInsight = JSON.parse(jsonMatch[0]);
        
        if (!parsedInsight.episodeTitle || !parsedInsight.description || !parsedInsight.books) {
          throw new Error('Invalid insight format: missing required fields');
        }
        setInsight(parsedInsight);
        
        if (data.mastodon?.url) {
          setMastodonUrl(data.mastodon.url);
        }
      } catch (parseError) {
        console.error('Parse error:', parseError);
        console.error('Raw response:', data.content[0].text);
        throw new Error('Failed to parse AI response: ' + parseError.message);
      }
    } catch (error) {
      console.error('Error:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ 
      maxWidth: '800px', 
      margin: '60px auto', 
      padding: '40px',
      backgroundColor: '#ffffff',
      minHeight: '100vh',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      <h1 style={{ 
        marginBottom: '40px',
        color: config.headerColor,
        fontSize: '2.5rem',
        fontWeight: '700'
      }}>{config.title}</h1>
      
      <div style={{ marginBottom: '40px' }}>
        <input
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder={config.placeholder}
          style={{ 
            width: '100%',
            padding: '16px',
            fontSize: '1.1rem',
            border: '2px solid #e5e5e5',
            borderRadius: '8px',
            backgroundColor: '#ffffff',
            color: '#1a1a1a',
            transition: 'all 0.2s ease',
            outline: 'none',
          }}
        />
        <button 
          onClick={generateInsight}
          disabled={loading || !topic}
          style={{
            marginTop: '20px',
            padding: '16px 32px',
            backgroundColor: config.headerColor,
            color: '#ffffff',
            border: 'none',
            borderRadius: '8px',
            fontSize: '1rem',
            fontWeight: '500',
            cursor: loading || !topic ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s ease',
            opacity: loading || !topic ? '0.5' : '1',
          }}
        >
          {loading ? 'Generating...' : 'Generate Insight'}
        </button>
        
        {error && (
          <div style={{
            marginTop: '20px',
            padding: '12px',
            backgroundColor: '#fee2e2',
            border: '1px solid #ef4444',
            borderRadius: '8px',
            color: '#dc2626',
            fontSize: '0.875rem'
          }}>
            {error}
          </div>
        )}

        {mastodonUrl && (
          <div style={{
            marginTop: '20px',
            padding: '12px',
            backgroundColor: '#f0f9ff',
            border: '1px solid #3b82f6',
            borderRadius: '8px',
            color: '#1e40af',
            fontSize: '0.875rem'
          }}>
            <a 
              href={mastodonUrl}
              target="_blank" 
              rel="noopener noreferrer"
              style={{
                color: '#2563eb',
                textDecoration: 'underline'
              }}
            >
              View on Mastodon
            </a>
          </div>
        )}
      </div>

      {insight && (
        <div style={{
          padding: '32px',
          backgroundColor: '#f8f8f8',
          borderRadius: '12px',
          marginTop: '40px'
        }}>
          <h2 style={{ 
            marginBottom: '20px',
            color: '#1a1a1a',
            fontSize: '1.5rem',
            fontWeight: '600'
          }}>{insight.episodeTitle}</h2>
          <p style={{ 
            marginBottom: '32px',
            color: '#4a4a4a',
            lineHeight: '1.6'
          }}>{insight.description}</p>
          
          <div style={{ marginTop: '32px' }}>
            <h3 style={{ 
              color: '#1a1a1a',
              fontSize: '1.2rem',
              fontWeight: '600',
              marginBottom: '16px'
            }}>Essential Reading</h3>
            
            <div style={{ marginTop: '16px' }}>
              <h4 style={{ 
                color: '#1a1a1a',
                fontSize: '1.1rem',
                fontWeight: '500',
                marginBottom: '8px'
              }}>Core Pattern:</h4>
              <p style={{ color: '#4a4a4a' }}>
                {insight.books.primary.title} by {insight.books.primary.author}
              </p>
              
              <h4 style={{ 
                marginTop: '24px',
                color: '#1a1a1a',
                fontSize: '1.1rem',
                fontWeight: '500',
                marginBottom: '8px'
              }}>Pattern Insights:</h4>
              <ul style={{ 
                color: '#4a4a4a',
                listStyleType: 'none',
                padding: 0
              }}>
                {insight.books.supporting.map((book, index) => (
                  <li key={index} style={{ marginBottom: '8px' }}>
                    {book.title} by {book.author}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;