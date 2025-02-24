from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional
import PyPDF2
import docx 

class DocumentNode:
    def __init__(self, content: str, level: int = 0, parent: Optional['DocumentNode'] = None):
        self.content = content
        self.level = level
        self.parent = parent
        self.children: List[DocumentNode] = []

    def add_child(self, child: 'DocumentNode'):
        child.parent = self
        self.children.append(child)

class DocumentLoader(ABC):
    """Base class for document loaders that parse PDF and Word documents into a tree structure"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"File {file_path} not found")
        
        self.root: Optional[DocumentNode] = None
        self._validate_file_type()

    @abstractmethod
    def _validate_file_type(self):
        """Validate that the file is of the correct type"""
        pass

    @abstractmethod
    def load(self) -> DocumentNode:
        """Load and parse the document into a tree structure"""
        pass

    @abstractmethod
    def _extract_text(self) -> str:
        """Extract raw text from the document"""
        pass

    @abstractmethod
    def _build_tree(self, text: str) -> DocumentNode:
        """Build a document tree from extracted text"""
        pass

    def get_tree(self) -> Optional[DocumentNode]:
        """Get the document tree, loading it if not already loaded"""
        if self.root is None:
            self.root = self.load()
        return self.root


class PDFLoader(DocumentLoader):
    """Loader for PDF documents"""
    
    def _validate_file_type(self):
        """Validate that the file is a PDF"""
        if not self.file_path.suffix == '.pdf':
            raise ValueError("File must be a PDF")
        
    def _extract_text(self) -> str:
        """Extract text from the PDF"""
        with open(self.file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ''
            for page in reader.pages:
                text += page.extract_text()
        return text
    
    def _build_tree(self, text: str) -> DocumentNode:
        """Build a document tree from extracted text"""
        # Split text into lines and create nodes based on indentation
        lines = text.split('\n')
        root = DocumentNode("Root")
        current_node = root
        
        for line in lines:
            if not line.strip():
                continue
                
            # Count leading spaces to determine level
            level = len(line) - len(line.lstrip())
            content = line.strip()
            
            # Create new node
            new_node = DocumentNode(content, level=level)
            
            # Find appropriate parent based on level
            while current_node.parent and current_node.level >= level:
                current_node = current_node.parent
                
            current_node.add_child(new_node)
            current_node = new_node
            
        return root
    
    def load(self) -> DocumentNode:
        """Load and parse the PDF document into a tree structure"""
        self._validate_file_type()
        text = self._extract_text()
        return self._build_tree(text)
    
class WordLoader(DocumentLoader):
    """Loader for Word documents"""
    
    def _validate_file_type(self):
        """Validate that the file is a Word document"""
        if not self.file_path.suffix == '.docx':
            raise ValueError("File must be a Word document")
        
    def _extract_text(self) -> str:
        """Extract text from the Word document"""
        doc = docx.Document(self.file_path)
        text = ''
        for paragraph in doc.paragraphs:
            text += paragraph.text + '\n'
        return text
    
    def _build_tree(self, text: str) -> DocumentNode:
        """Build a document tree from extracted text"""
        root = DocumentNode(text)

        return root
    
    def load(self) -> DocumentNode:
        """Load and parse the Word document into a tree structure"""
        self._validate_file_type()
        text = self._extract_text()
        return self._build_tree(text)
