import React from 'react';

interface MarkdownRendererProps {
  content: string;
}

const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content }) => {
  const renderMarkdown = (text: string) => {
    // Split by lines to process each line
    const lines = text.split('\n');
    const elements: JSX.Element[] = [];
    let currentParagraph: string[] = [];
    let key = 0;

    const flushParagraph = () => {
      if (currentParagraph.length > 0) {
        const paragraphText = currentParagraph.join(' ').trim();
        if (paragraphText) {
          elements.push(
            <p key={`p-${key++}`} className="mb-4 text-gray-700 leading-relaxed">
              {renderInlineMarkdown(paragraphText)}
            </p>
          );
        }
        currentParagraph = [];
      }
    };

    lines.forEach((line) => {
      const trimmedLine = line.trim();
      
      // Headers
      if (trimmedLine.startsWith('### ')) {
        flushParagraph();
        elements.push(
          <h3 key={`h3-${key++}`} className="text-xl font-bold text-gray-900 mb-3 mt-6">
            {trimmedLine.slice(4)}
          </h3>
        );
      } else if (trimmedLine.startsWith('#### ')) {
        flushParagraph();
        elements.push(
          <h4 key={`h4-${key++}`} className="text-lg font-semibold text-gray-800 mb-2 mt-4">
            {trimmedLine.slice(5)}
          </h4>
        );
      } else if (trimmedLine.startsWith('## ')) {
        flushParagraph();
        elements.push(
          <h2 key={`h2-${key++}`} className="text-2xl font-bold text-gray-900 mb-4 mt-6">
            {trimmedLine.slice(3)}
          </h2>
        );
      } else if (trimmedLine.startsWith('# ')) {
        flushParagraph();
        elements.push(
          <h1 key={`h1-${key++}`} className="text-3xl font-bold text-gray-900 mb-4 mt-6">
            {trimmedLine.slice(2)}
          </h1>
        );
      }
      // List items
      else if (trimmedLine.match(/^[\d]+\.\s/)) {
        flushParagraph();
        const listContent = trimmedLine.replace(/^[\d]+\.\s/, '');
        elements.push(
          <div key={`ol-${key++}`} className="mb-2">
            <ol className="list-decimal list-inside">
              <li className="text-gray-700 leading-relaxed">
                {renderInlineMarkdown(listContent)}
              </li>
            </ol>
          </div>
        );
      } else if (trimmedLine.startsWith('- ') || trimmedLine.startsWith('• ')) {
        flushParagraph();
        const listContent = trimmedLine.slice(2);
        elements.push(
          <div key={`ul-${key++}`} className="mb-2">
            <ul className="list-disc list-inside">
              <li className="text-gray-700 leading-relaxed">
                {renderInlineMarkdown(listContent)}
              </li>
            </ul>
          </div>
        );
      }
      // Code blocks (simplified)
      else if (trimmedLine.startsWith('```')) {
        flushParagraph();
        // Skip for now, could be enhanced
      }
      // Empty lines
      else if (trimmedLine === '') {
        flushParagraph();
      }
      // Regular content
      else {
        currentParagraph.push(line);
      }
    });

    // Flush any remaining paragraph
    flushParagraph();

    return elements;
  };

  const renderInlineMarkdown = (text: string): JSX.Element => {
    // Handle bold text
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Handle italic text
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Handle inline code
    text = text.replace(/`(.*?)`/g, '<code class="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono">$1</code>');

    // Handle mathematical expressions (basic LaTeX)
    text = text.replace(/\\\[(.*?)\\\]/g, '<div class="bg-gray-50 p-2 my-2 rounded font-mono text-sm">$1</div>');
    text = text.replace(/\\\((.*?)\\\)/g, '<span class="font-mono bg-gray-50 px-1 rounded">$1</span>');

    return (
      <span
        dangerouslySetInnerHTML={{ __html: text }}
      />
    );
  };

  return (
    <div className="prose prose-gray max-w-none">
      {renderMarkdown(content)}
    </div>
  );
};

export default MarkdownRenderer;