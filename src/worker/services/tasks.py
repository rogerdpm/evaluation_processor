from worker.eval_app import celery_app
from worker.utils.document_loader import PDFLoader, WordLoader
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

@celery_app.task
def run_evaluation(document_path: str):
    print(f"Evaluating document {document_path}")
    with tracer.start_as_current_span("run_evaluation") as span:
        # Determine file type and use appropriate loader    
        span.set_attribute("document_path", document_path)

    # Determine file type and use appropriate loader
    if document_path.endswith('.pdf'):
        loader = PDFLoader(document_path)
    elif document_path.endswith('.docx'):
        loader = WordLoader(document_path)
    else:
        raise ValueError("Unsupported document type. Must be PDF or Word document.")

    # Load and parse the document
    document_tree = loader.get_tree()
    
    def print_node(node, level=0):
        indent = "  " * level
        print(f"{indent}Node attributes:")
        print(f"{indent}- content: {node.content}")
        print(f"{indent}- level: {node.level}")
        print(f"{indent}- parent: {node.parent}")
        print(f"{indent}- children count: {len(node.children)}")
        print(f"{indent}Content: {node.content}")
        if hasattr(node, 'children'):
            for child in node.children:
                print_node(child, level + 1)

    # Print the full document tree structure
    print("\nDocument Tree Structure:")
    print_node(document_tree)
    return document_tree.content

