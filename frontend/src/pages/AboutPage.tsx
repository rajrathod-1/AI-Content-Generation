import React from 'react';
import { motion } from 'framer-motion';
import { 
  LightBulbIcon,
  MagnifyingGlassIcon,
  DocumentTextIcon,
  LinkIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowPathIcon,
  CircleStackIcon
} from '@heroicons/react/24/outline';

const AboutPage: React.FC = () => {
  const ragSteps = [
    {
      step: 1,
      title: "Query Processing",
      description: "User's question is analyzed and converted into vector embeddings",
      icon: <MagnifyingGlassIcon className="h-6 w-6" />
    },
    {
      step: 2,
      title: "Knowledge Retrieval",
      description: "Relevant documents are retrieved from vector database using semantic search",
      icon: <CircleStackIcon className="h-6 w-6" />
    },
    {
      step: 3,
      title: "Web Crawling",
      description: "Real-time web crawling fetches latest information on the topic",
      icon: <ArrowPathIcon className="h-6 w-6" />
    },
    {
      step: 4,
      title: "Context Augmentation",
      description: "Retrieved information is combined to create enriched context",
      icon: <DocumentTextIcon className="h-6 w-6" />
    },
    {
      step: 5,
      title: "Response Generation",
      description: "AI generates accurate response based on retrieved context",
      icon: <LightBulbIcon className="h-6 w-6" />
    }
  ];

  const comparison = [
    {
      feature: "Knowledge Cutoff",
      rag: "Real-time web data",
      chatgpt: "Training data only (Static)",
      ragBetter: true
    },
    {
      feature: "Source Citations",
      rag: "Provides source links",
      chatgpt: "No source attribution",
      ragBetter: true
    },
    {
      feature: "Accuracy",
      rag: "Grounded in retrieved facts",
      chatgpt: "May hallucinate information",
      ragBetter: true
    },
    {
      feature: "Customization",
      rag: "Custom knowledge base",
      chatgpt: "Fixed training data",
      ragBetter: true
    },
    {
      feature: "Context Relevance",
      rag: "Domain-specific retrieval",
      chatgpt: "General knowledge only",
      ragBetter: true
    },
    {
      feature: "Cost Efficiency",
      rag: "Lower operational costs",
      chatgpt: "Higher API costs",
      ragBetter: true
    }
  ];

  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section */}
      <section className="py-20 bg-gradient-to-br from-blue-50 via-white to-cyan-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-center"
          >
            <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
              Understanding 
              <span className="bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">
                {" "}Retrieval-Augmented Generation
              </span>
            </h1>
            <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
              Discover how RAG revolutionizes AI by combining the power of real-time information 
              retrieval with advanced language generation capabilities.
            </p>
          </motion.div>
        </div>
      </section>

      {/* What is RAG Section */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-6">
              What is RAG?
            </h2>
            <div className="max-w-4xl mx-auto">
              <p className="text-lg text-gray-600 mb-8">
                Retrieval-Augmented Generation (RAG) is an advanced AI architecture that enhances 
                large language models by giving them access to external knowledge sources. Unlike 
                traditional AI models that rely solely on their training data, RAG systems can 
                dynamically retrieve and incorporate relevant information from databases, documents, 
                and the web to generate more accurate and up-to-date responses.
              </p>
              <div className="bg-blue-50 rounded-2xl p-8 text-left">
                <h3 className="text-xl font-semibold text-blue-900 mb-4">Key Benefits:</h3>
                <ul className="space-y-3 text-blue-800">
                  <li className="flex items-center">
                    <CheckCircleIcon className="h-5 w-5 text-blue-600 mr-3 flex-shrink-0" />
                    <span>Always up-to-date information through real-time retrieval</span>
                  </li>
                  <li className="flex items-center">
                    <CheckCircleIcon className="h-5 w-5 text-blue-600 mr-3 flex-shrink-0" />
                    <span>Reduced hallucinations with fact-based responses</span>
                  </li>
                  <li className="flex items-center">
                    <CheckCircleIcon className="h-5 w-5 text-blue-600 mr-3 flex-shrink-0" />
                    <span>Transparent source attribution and citations</span>
                  </li>
                  <li className="flex items-center">
                    <CheckCircleIcon className="h-5 w-5 text-blue-600 mr-3 flex-shrink-0" />
                    <span>Customizable knowledge base for specific domains</span>
                  </li>
                </ul>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* How RAG Works */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-6">
              How RAG Works
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Our RAG system follows a sophisticated 5-step process to deliver accurate, 
              contextual responses backed by real-time data.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8">
            {ragSteps.map((step, index) => (
              <motion.div
                key={step.step}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
                className="relative"
              >
                {/* Connection Line */}
                {index < ragSteps.length - 1 && (
                  <div className="hidden lg:block absolute top-12 left-full w-full h-0.5 bg-blue-200 transform translate-x-4 z-0"></div>
                )}
                
                <div className="card text-center relative z-10">
                  <div className="w-12 h-12 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
                    {step.icon}
                  </div>
                  <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center mx-auto mb-4 text-sm font-bold">
                    {step.step}
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {step.title}
                  </h3>
                  <p className="text-gray-600 text-sm">
                    {step.description}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* RAG vs ChatGPT Comparison */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-6">
              RAG vs Standard ChatGPT
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              See how our RAG system compares to traditional language models across key metrics
            </p>
          </motion.div>

          <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Feature</th>
                    <th className="px-6 py-4 text-center text-sm font-semibold text-blue-600">RAG System</th>
                    <th className="px-6 py-4 text-center text-sm font-semibold text-red-600">Standard ChatGPT</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {comparison.map((item, index) => (
                    <motion.tr
                      key={index}
                      initial={{ opacity: 0, x: -20 }}
                      whileInView={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.5, delay: index * 0.1 }}
                      viewport={{ once: true }}
                      className="hover:bg-gray-50"
                    >
                      <td className="px-6 py-4 text-sm font-medium text-gray-900">
                        {item.feature}
                      </td>
                      <td className="px-6 py-4 text-center">
                        <div className="flex items-center justify-center space-x-2">
                          <CheckCircleIcon className="h-5 w-5 text-green-500" />
                          <span className="text-sm text-gray-700">{item.rag}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <div className="flex items-center justify-center space-x-2">
                          <XCircleIcon className="h-5 w-5 text-red-500" />
                          <span className="text-sm text-gray-700">{item.chatgpt}</span>
                        </div>
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </section>

      {/* Technical Architecture */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-6">
              Technical Architecture
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Our system leverages cutting-edge technologies to deliver superior performance
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              viewport={{ once: true }}
              className="card"
            >
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Vector Database</h3>
              <p className="text-gray-600 mb-4">
                FAISS (Facebook AI Similarity Search) for efficient semantic search and similarity matching.
              </p>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• High-performance vector indexing</li>
                <li>• Real-time similarity search</li>
                <li>• Scalable to millions of documents</li>
              </ul>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              viewport={{ once: true }}
              className="card"
            >
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Embeddings Model</h3>
              <p className="text-gray-600 mb-4">
                Advanced sentence transformers for converting text into high-dimensional vectors.
              </p>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Semantic understanding</li>
                <li>• Multi-language support</li>
                <li>• Context-aware embeddings</li>
              </ul>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              viewport={{ once: true }}
              className="card"
            >
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Web Crawling</h3>
              <p className="text-gray-600 mb-4">
                Intelligent web crawlers that fetch and process real-time information from various sources.
              </p>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Respectful crawling policies</li>
                <li>• Content deduplication</li>
                <li>• Quality filtering</li>
              </ul>
            </motion.div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default AboutPage;