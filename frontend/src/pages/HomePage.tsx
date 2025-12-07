import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  SparklesIcon, 
  MagnifyingGlassIcon, 
  DocumentTextIcon,
  ChartBarIcon,
  ArrowRightIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';

const HomePage: React.FC = () => {
  const features = [
    {
      icon: <SparklesIcon className="h-6 w-6" />,
      title: "RAG-Powered Generation",
      description: "Combines retrieval with generation for contextually accurate responses that go beyond simple ChatGPT interactions."
    },
    {
      icon: <MagnifyingGlassIcon className="h-6 w-6" />,
      title: "Real-time Web Crawling",
      description: "Automatically fetches fresh data from the internet to ensure responses are current and relevant."
    },
    {
      icon: <DocumentTextIcon className="h-6 w-6" />,
      title: "Semantic Search",
      description: "Uses advanced vector embeddings to find contextually similar content across your knowledge base."
    },
    {
      icon: <ChartBarIcon className="h-6 w-6" />,
      title: "Performance Analytics",
      description: "Real-time metrics and monitoring to track system performance and response quality."
    }
  ];

  const advantages = [
    "Gets latest information through web crawling",
    "Provides source citations for transparency",
    "Maintains context across conversations",
    "Reduces hallucinations with grounded responses",
    "Customizable knowledge base",
    "Cost-effective compared to fine-tuning"
  ];

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative py-20 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-50 via-white to-cyan-50"></div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-center"
          >
            <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
              The Future of
              <span className="bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">
                {" "}AI Content Generation
              </span>
            </h1>
            <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
              Experience the power of Retrieval-Augmented Generation (RAG) - an intelligent AI system 
              that combines real-time web crawling with advanced semantic search to deliver accurate, 
              contextual, and up-to-date responses.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                to="/chat"
                className="btn-primary text-lg px-8 py-4 flex items-center justify-center space-x-2"
              >
                <span>Try RAG Assistant</span>
                <ArrowRightIcon className="h-5 w-5" />
              </Link>
              <Link
                to="/about"
                className="btn-outline text-lg px-8 py-4"
              >
                Learn About RAG
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Why Choose RAG Over Standard ChatGPT?
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Our RAG system provides significant advantages over traditional language models
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
                className="card hover:shadow-lg transition-shadow duration-300"
              >
                <div className="flex items-center justify-center w-12 h-12 bg-blue-100 text-blue-600 rounded-lg mb-4">
                  {feature.icon}
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-600">
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Advantages Section */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8 }}
              viewport={{ once: true }}
            >
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-6">
                RAG Advantages Over ChatGPT
              </h2>
              <p className="text-lg text-gray-600 mb-8">
                While ChatGPT is trained on static data with a knowledge cutoff, our RAG system 
                continuously updates its knowledge base through real-time web crawling and semantic search.
              </p>
              <ul className="space-y-4">
                {advantages.map((advantage, index) => (
                  <motion.li
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.5, delay: index * 0.1 }}
                    viewport={{ once: true }}
                    className="flex items-center space-x-3"
                  >
                    <CheckCircleIcon className="h-5 w-5 text-green-500 flex-shrink-0" />
                    <span className="text-gray-700">{advantage}</span>
                  </motion.li>
                ))}
              </ul>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8 }}
              viewport={{ once: true }}
              className="relative"
            >
              <div className="bg-white rounded-2xl shadow-xl p-8">
                <div className="space-y-6">
                  <div className="flex items-center space-x-4">
                    <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
                      <span className="text-red-600 font-bold">GPT</span>
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">Standard ChatGPT</h3>
                      <p className="text-sm text-gray-500">Knowledge cutoff: Training data only</p>
                    </div>
                  </div>
                  <div className="border-t pt-6">
                    <div className="flex items-center space-x-4">
                      <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                        <span className="text-blue-600 font-bold">RAG</span>
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-900">Our RAG System</h3>
                        <p className="text-sm text-gray-500">Real-time knowledge: Always up-to-date</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-blue-600 to-cyan-600">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
          >
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
              Ready to Experience the Difference?
            </h2>
            <p className="text-xl text-blue-100 mb-8">
              See how RAG-powered AI delivers more accurate, contextual, and up-to-date responses
            </p>
            <Link
              to="/chat"
              className="inline-flex items-center px-8 py-4 bg-white text-blue-600 font-semibold rounded-lg hover:bg-gray-50 transition-colors duration-200 space-x-2"
            >
              <span>Start Chatting Now</span>
              <ArrowRightIcon className="h-5 w-5" />
            </Link>
          </motion.div>
        </div>
      </section>
    </div>
  );
};

export default HomePage;