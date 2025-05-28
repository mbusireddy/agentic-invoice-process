# Invoice Processing System - Project Structure

```
invoice_processing_system/
├── requirements.txt
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── regional_rules.py
├── agents/
│   ├── __init__.py
│   ├── base_agent.py
│   ├── document_parser_agent.py
│   ├── data_extraction_agent.py
│   ├── validation_agent.py
│   ├── regional_compliance_agent.py
│   ├── approval_agent.py
│   └── audit_agent.py
├── models/
│   ├── __init__.py
│   ├── invoice_model.py
│   └── processing_result.py
├── utils/
│   ├── __init__.py
│   ├── llama_index_manager.py
│   ├── ollama_client.py
│   └── document_processor.py
├── orchestrator/
│   ├── __init__.py
│   ├── workflow_manager.py
│   └── agent_coordinator.py
├── ui/
│   ├── __init__.py
│   ├── streamlit_app.py
│   └── components/
│       ├── __init__.py
│       ├── upload_component.py
│       ├── results_component.py
│       └── dashboard_component.py
├── data/
│   ├── invoices/
│   ├── processed/
│   └── index/
├── logs/
└── main.py
```

## Key Components Overview

### 1. **Agents Layer**
- Specialized AI agents for different processing stages
- Each agent has specific responsibilities and expertise
- Agents communicate through a structured message passing system

### 2. **Orchestration Layer**
- LangGraph-based workflow management
- Agent coordination and task routing
- State management across processing pipeline

### 3. **Data Layer**
- LlamaIndex for document indexing and retrieval
- Ollama for embeddings and local LLM inference
- Structured data models for invoice processing

### 4. **UI Layer**
- Streamlit-based web interface
- Real-time processing visualization
- Interactive dashboard for monitoring

### 5. **Configuration Layer**
- Regional rule definitions
- System settings and parameters
- Agent behavior configuration