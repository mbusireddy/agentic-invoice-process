"""
Main Entry Point - Invoice Processing System

This is the main entry point for the invoice processing system.
It provides both CLI and web interfaces for processing invoices.
"""
import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional

from config.settings import settings, create_directories
from orchestrator import AgentCoordinator, WorkflowManager, WorkflowType


def setup_logging():
    """Set up logging configuration"""
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format=settings.LOG_FORMAT,
        handlers=[
            logging.FileHandler(settings.LOGS_DIR / "system.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )


def run_cli_processing(files: List[str], workflow: str, batch: bool = False):
    """Run processing via CLI"""
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize components
        logger.info("Initializing processing components...")
        agent_coordinator = AgentCoordinator()
        workflow_manager = WorkflowManager(agent_coordinator)
        
        # Validate workflow type
        if workflow not in workflow_manager.get_available_workflows():
            logger.error(f"Unknown workflow type: {workflow}")
            available = workflow_manager.get_available_workflows()
            logger.error(f"Available workflows: {', '.join(available)}")
            return False
        
        # Process files
        if batch and len(files) > 1:
            logger.info(f"Starting batch processing of {len(files)} files with workflow '{workflow}'")
            
            # Use agent coordinator's batch processing
            batch_result = agent_coordinator.process_batch(files)
            
            # Print results
            print(f"\nBatch Processing Results:")
            print(f"Total files: {batch_result['total_files']}")
            print(f"Processed: {batch_result['processed']}")
            print(f"Successful: {batch_result['successful']}")
            print(f"Failed: {batch_result['failed']}")
            print(f"Pending Review: {batch_result['pending_review']}")
            print(f"Processing time: {batch_result['processing_time']:.2f}s")
            
        else:
            # Process individual files
            for file_path in files:
                logger.info(f"Processing file: {file_path}")
                
                result = workflow_manager.execute_workflow(
                    workflow_type=workflow,
                    input_data=file_path
                )
                
                # Print results
                print(f"\nProcessing Results for {Path(file_path).name}:")
                print(f"Status: {result['status']}")
                print(f"Confidence: {result['confidence_score']:.1%}")
                print(f"Processing time: {result['processing_time']:.2f}s")
                print(f"Errors: {len(result['errors'])}")
                print(f"Warnings: {len(result['warnings'])}")
                
                if result['errors']:
                    print("Errors:")
                    for error in result['errors']:
                        print(f"  - {error}")
                
                if result['invoice']:
                    invoice = result['invoice']
                    print(f"Invoice Number: {invoice.invoice_number}")
                    print(f"Vendor: {invoice.vendor_name}")
                    print(f"Total: {invoice.currency} {invoice.total_amount:,.2f}")
        
        return True
        
    except Exception as e:
        logger.error(f"CLI processing failed: {e}")
        return False


def run_web_interface():
    """Run the Streamlit web interface"""
    import subprocess
    import sys
    
    try:
        # Run Streamlit app
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "ui/streamlit_app.py",
            "--server.port", str(settings.STREAMLIT_PORT),
            "--server.headless", "true" if not settings.DEBUG_MODE else "false"
        ])
    except KeyboardInterrupt:
        print("\nShutting down web interface...")
    except Exception as e:
        print(f"Failed to start web interface: {e}")


def run_system_health_check():
    """Run system health check"""
    logger = logging.getLogger(__name__)
    
    try:
        agent_coordinator = AgentCoordinator()
        health = agent_coordinator.get_system_health()
        
        print("System Health Check Results:")
        print(f"Overall Status: {health['overall_status']}")
        print(f"Healthy Agents: {health['healthy_agents']}/{health['total_agents']}")
        print(f"Ollama Connected: {health['ollama_connected']}")
        
        if health['overall_status'] != 'healthy':
            print("\nAgent Details:")
            for agent_name, details in health['agent_details'].items():
                status = details['health']['status']
                print(f"  {agent_name}: {status}")
                if details['health'].get('issues'):
                    for issue in details['health']['issues']:
                        print(f"    - {issue}")
        
        return health['overall_status'] == 'healthy'
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        print(f"Health check failed: {e}")
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Invoice Processing System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start web interface
  python main.py web
  
  # Process single file
  python main.py process invoice.pdf
  
  # Process multiple files with fast track workflow
  python main.py process *.pdf --workflow fast_track
  
  # Batch process files
  python main.py process *.pdf --batch
  
  # Run health check
  python main.py health
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Web interface command
    web_parser = subparsers.add_parser('web', help='Start web interface')
    
    # Processing command
    process_parser = subparsers.add_parser('process', help='Process invoice files')
    process_parser.add_argument('files', nargs='+', help='Invoice files to process')
    process_parser.add_argument(
        '--workflow', 
        default=WorkflowType.STANDARD.value,
        choices=[wf.value for wf in WorkflowType],
        help='Workflow type to use'
    )
    process_parser.add_argument(
        '--batch', 
        action='store_true',
        help='Process files as a batch'
    )
    
    # Health check command
    health_parser = subparsers.add_parser('health', help='Run system health check')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Set up environment
    create_directories()
    setup_logging()
    
    # Execute command
    if args.command == 'web' or not args.command:
        print("Starting Invoice Processing System Web Interface...")
        print(f"Open your browser to: http://localhost:{settings.STREAMLIT_PORT}")
        run_web_interface()
        
    elif args.command == 'process':
        success = run_cli_processing(args.files, args.workflow, args.batch)
        sys.exit(0 if success else 1)
        
    elif args.command == 'health':
        healthy = run_system_health_check()
        sys.exit(0 if healthy else 1)
        
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()