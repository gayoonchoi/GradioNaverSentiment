import { useState } from 'react';
import { FaChevronDown, FaChevronUp } from 'react-icons/fa';
import ReactMarkdown from 'react-markdown';

interface ExplanationToggleProps {
  title: string;
  content: string; // Markdown string
}

export default function ExplanationToggle({ title, content }: ExplanationToggleProps) {
  const [isOpen, setIsOpen] = useState(false);

  if (!content || content.length === 0) {
    return null; // Don't render if there's no content
  }

  return (
    <div className="mt-2 mb-4 border-t border-gray-200 pt-2">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between w-full text-left text-sm font-medium text-gray-600 hover:text-gray-800 focus:outline-none"
      >
        <span>{title}</span>
        {isOpen ? <FaChevronUp className="ml-2" /> : <FaChevronDown className="ml-2" />}
      </button>
      {isOpen && (
        <div className="mt-2 p-3 bg-gray-50 rounded-md text-xs text-gray-700 prose max-w-none">
          <ReactMarkdown>{content}</ReactMarkdown>
        </div>
      )}
    </div>
  );
}
