from graphviz import Digraph
from typing import Dict, List, Union, Any, Iterator, TextIO
import os
from datetime import datetime
import json
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import PIL.Image
 
def parse_indented_text(filepath: str) -> Dict[str, Any]:
    """Previous parse_indented_text function remains the same"""
    def get_indent_level(line: str) -> int:
        return (len(line) - len(line.lstrip())) // 4
    
    def is_leaf_node(lines: List[str], current_idx: int, current_indent: int) -> bool:
        if current_idx + 1 >= len(lines):
            return True
        next_indent = get_indent_level(lines[current_idx + 1])
        return next_indent <= current_indent
    
    def process_lines(lines: List[str], start_idx: int, min_indent: int) -> tuple[Dict[str, Any], int]:
        result = {}
        i = start_idx
        
        while i < len(lines):
            line = lines[i].rstrip()
            if not line:
                i += 1
                continue
                
            indent = get_indent_level(line)
            if indent < min_indent:
                break
                
            key = line.strip()
            if is_leaf_node(lines, i, indent):
                result[key] = []
            else:
                nested_dict, new_i = process_lines(lines, i + 1, indent + 1)
                result[key] = nested_dict
                i = new_i - 1
            i += 1
            
        return result, i
    
    with open(filepath, 'r') as file:
        lines = [line.rstrip('\n').replace(':','') for line in file if line.strip()]
    
    result, _ = process_lines(lines, 0, 0)
    return result

# Previous helper functions remain the same
def save_dict_to_json(data: Dict[str, Any], output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    json_path = os.path.join(output_dir, "structure.json")
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)
    return json_path

def chunk_dictionary(data: Dict[str, Any], chunk_size: int) -> Iterator[Dict[str, Any]]:
    items = list(data.items())
    for i in range(0, len(items), chunk_size):
        chunk = dict(items[i:i + chunk_size])
        yield chunk

def create_digraph_from_nested_dict(data: Dict[str, Union[Dict, List]], 
                                  graph_name: str = "nested_dict_graph") -> Digraph:
    """Previous create_digraph_from_nested_dict function remains the same"""
    dot = Digraph(name=graph_name,node_attr={'shape':'plain','font_color':'red'})
    dot.attr(rankdir='LR')
    
    def process_node(current_dict: Union[Dict, List], 
                    parent_key: str = None, 
                    path: str = "") -> None:
        if isinstance(current_dict, dict):
            for key, value in current_dict.items():
                current_path = f"{path}_{key}" if path else key
                dot.node(current_path, key)
                
                if parent_key:
                    dot.edge(path, current_path)
                
                process_node(value, key, current_path)
                
        elif isinstance(current_dict, list):
            for i, item in enumerate(current_dict):
                node_id = f"{path}_item_{i}"
                dot.node(node_id, str(item))
                dot.edge(path, node_id)

    process_node(data)
    return dot

def create_output_directory() -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"C:\\Users\\thoopal\\Vea Tinkerzone 2025\\graph_output_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def compile_graphs_to_pdf(metadata: Dict[str, Any], output_dir: str) -> str:
    """
    Compiles all generated graphs into a single PDF with metadata and structure information.
    
    Args:
        metadata: Dictionary containing process metadata
        output_dir: Directory where the PDF should be saved
        
    Returns:
        Path to the generated PDF file
    """
    pdf_path = os.path.join(output_dir, "concept_map.pdf")
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Prepare styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12
    )
    normal_style = styles['Normal']
    
    # Build PDF content
    content = []
    
    # Title
    content.append(Paragraph("Text Book Concept Map", title_style))
    content.append(Spacer(1, 20))
    
    # Metadata section
    content.append(Paragraph("Process Information", heading_style))
    metadata_table = [
        ["Input File", metadata['input_file']],
        ["Total Keys", str(metadata['total_keys'])],
        ["Chunk Size", str(metadata['chunk_size'])],
        ["Generation Time", metadata['timestamp']]
    ]
    
    t = Table(metadata_table, colWidths=[2*inch, 4*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.red),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    content.append(t)
    content.append(Spacer(1, 30))
    
    # Graphs section
    content.append(Paragraph("Generated Concept Maps", heading_style))
    content.append(Spacer(1, 20))
    
    # Add each graph with its metadata
    for chunk in metadata['chunks']:
        # Chunk header
        content.append(Paragraph(f"Chunk {chunk['chunk_number']}", heading_style))
        content.append(Paragraph(f"Keys: {', '.join(chunk['keys'])}", normal_style))
        content.append(Spacer(1, 10))
        
        # Add the graph image
        if os.path.exists(chunk['file_path']):
            # Resize image if necessary
            img = PIL.Image.open(chunk['file_path'])
            aspect = img.width / img.height
            
            # Calculate dimensions to fit on page
            max_width = 6 * inch  # 6 inches maximum width
            max_height = 8 * inch  # 8 inches maximum height
            
            if aspect > 1:  # Wider than tall
                width = min(max_width, img.width)
                height = width / aspect
            else:  # Taller than wide
                height = min(max_height, img.height)
                width = height * aspect
            
            content.append(Image(chunk['file_path'], width=width, height=height))
        else:
            content.append(Paragraph("Graph image not found", normal_style))
        
        content.append(PageBreak())
    
    # Build the PDF
    doc.build(content)
    return pdf_path

def process_text_to_graphs(input_filepath: str, 
                         chunk_size: int = 4,
                         output_format: str = "png") -> Dict[str, Any]:
    """
    Main function to process text file to graphs and compile PDF.
    
    Args:
        input_filepath: Path to the indented text file
        chunk_size: Number of root keys per 
        output_format: Format for the output graphs
        
    Returns:
        Dictionary containing all output paths and metadata
    """
    # Create output directory
    output_dir = create_output_directory()
    
    # Parse text file to dictionary
    nested_dict = parse_indented_text(input_filepath)
    
    # Save dictionary to JSON
    json_path = save_dict_to_json(nested_dict, output_dir)
    
    # Initialize metadata
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "input_file": input_filepath,
        "json_structure": json_path,
        "total_keys": len(nested_dict),
        "chunk_size": chunk_size,
        "chunks": [],
        "graph_files": []
    }
    
    # Process each chunk
    for i, chunk in enumerate(chunk_dictionary(nested_dict, chunk_size)):
        # Create graph for this chunk
        graph = create_digraph_from_nested_dict(chunk)
        
        # Generate output path
        output_base = os.path.join(output_dir, f"graph_chunk_{i+1}")
        output_path = f"{output_base}.{output_format}"
        
        # Render the graph
        graph.render(output_base, format=output_format, cleanup=True)
        
        # Add chunk metadata
        metadata["chunks"].append({
            "chunk_number": i + 1,
            "keys": list(chunk.keys()),
            "file_path": output_path
        })
        metadata["graph_files"].append(output_path)
    
    # Compile PDF
    pdf_path = compile_graphs_to_pdf(metadata, output_dir)
    metadata["pdf_path"] = pdf_path
    
    # Save metadata
    metadata_path = os.path.join(output_dir, "process_metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    
    return metadata

# Example usage
def main():

    # Process the file
    metadata = process_text_to_graphs(
        input_filepath="C:\\Users\\thoopal\\Vea Tinkerzone 2025\\Full_Book_Summary.txt",
        chunk_size=2,
        output_format="png"
    )
    
    print("\nProcessing complete! Check the following locations:")
    print(f"- JSON structure: {metadata['json_structure']}")
    print(f"- PDF compilation: {metadata['pdf_path']}")
    print(f"- Individual graphs: {', '.join(metadata['graph_files'])}")
    print(f"- Full metadata: {os.path.dirname(metadata['json_structure'])}/process_metadata.json")

if __name__ == "__main__":
    main()