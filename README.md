# RankFusion-RAG: Secure Document Assistant

**An Intelligent Document Retrieval and Citation Ranking Framework for Multi-Document Question Answering**

## Overview

RankFusion-RAG is an intelligent document-based question-answering system that enables users to upload, organize, search, and retrieve information from multiple PDF documents.

The system combines Retrieval-Augmented Generation (RAG) with a document-aware ranking and evidence reranking framework to improve the relevance of retrieved information and provide context-grounded answers with supporting citations.

Unlike conventional RAG systems that directly select the most similar text chunks, RankFusion-RAG evaluates candidate information at the document level before selecting the final evidence for answer generation.

The application is designed to provide a secure and interactive environment for querying personal document collections without relying on external web searches.

## Key Features

- **User Authentication:** Secure login, registration, and password reset functionality.
- **Document Management:** Upload and organize PDF documents into folders.
- **PDF Processing:** Extract text, identify pages, and divide documents into manageable text chunks.
- **Semantic Search:** Retrieve relevant document content using embedding-based similarity search.
- **RankFusion-RAG Framework:** Retrieve candidate chunks, group them by source document, calculate document-level relevance scores, and rerank documents before selecting final evidence.
- **AI-Powered Answers:** Generate context-grounded answers using Google's Gemini models.
- **Citation-Based Responses:** Display primary and supporting citations with document names, page numbers, and relevant text.
- **PDF Citation Highlighting:** Highlight cited text directly within the corresponding PDF pages.
- **Multi-Document Question Answering:** Ask questions across multiple uploaded documents.
- **Document Comparison:** Compare retrieval and answer-generation performance between Standard RAG and RankFusion-RAG.
- **Chat History:** Maintain conversations associated with document folders.

## How RankFusion-RAG Works

The framework introduces a document-aware ranking stage into the conventional RAG pipeline.

### Retrieval and Ranking Pipeline

1. **Document Upload:** Users upload PDF documents to the application.
2. **Text Extraction:** The system extracts document text and divides it into smaller chunks.
3. **Embedding Generation:** Text chunks are converted into vector embeddings.
4. **Candidate Retrieval:** The semantic search component retrieves relevant candidate chunks.
5. **Document Grouping:** Retrieved chunks are grouped according to their source documents.
6. **Document-Level Scoring:** Documents are evaluated using their best similarity score, average similarity score, and candidate chunk count.
7. **Document Reranking:** Documents are ranked based on their combined relevance.
8. **Evidence Selection:** Relevant evidence chunks are selected from the reranked documents.
9. **Answer Generation:** The selected evidence is provided to Gemini to generate a context-grounded response.
10. **Citation Presentation:** The answer is displayed along with supporting document references and page-level citations.

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | React.js |
| Build Tool | Vite |
| Backend | Python, FastAPI |
| Database | Supabase PostgreSQL |
| Authentication | Supabase Auth |
| File Storage | Supabase Storage |
| AI / LLM | Google Gemini |
| Embeddings | Gemini Embedding Models |
| PDF Processing | PyMuPDF, PDF.js |
| Semantic Retrieval | Vector Similarity Search |

## System Architecture

The application follows a frontend-backend architecture.

- **Frontend:** Provides the user interface for authentication, document uploads, folder management, PDF viewing, and AI-powered conversations.
- **Backend:** Handles document processing, text extraction, embedding generation, semantic retrieval, ranking, and answer generation.
- **Database:** Stores user information, document metadata, document chunks, and vector embeddings.
- **AI Integration:** Uses Gemini for embedding generation and context-based answer generation.
- **Storage:** Stores uploaded PDF documents.

## Performance Evaluation

The framework was evaluated by comparing Standard RAG and RankFusion-RAG across multiple academic document datasets.

The evaluation considered:

- Answer Relevance
- Context Relevance
- Citation Correctness
- Faithfulness
- Overall Score
- Answer Accuracy
- Citation Accuracy
- Retrieval Precision
- Retrieval and response time

The comparison helps analyze the effectiveness of document-aware ranking in multi-document question-answering scenarios.

## Security and Reliability

- User authentication and access management.
- Organized document storage.
- Context-grounded answer generation.
- Similarity threshold-based retrieval.
- Fallback responses when relevant information is not found in the uploaded documents.
- Document-based citations to support answer verification.

## Project Objective

The primary objective of RankFusion-RAG is to improve document retrieval and evidence selection in multi-document question-answering systems by introducing document-level relevance scoring and reranking.

The project explores how combining semantic similarity with document-aware ranking can improve the quality and reliability of retrieved evidence.

## Future Enhancements

- Advanced hybrid retrieval techniques.
- Improved document ranking strategies.
- Support for additional document formats.
- Retrieval optimization for large document collections.
- Enhanced evaluation and benchmarking.

## Author

**G. Yazhini**  
Integrated M.Tech – Software Engineering  
Vellore Institute of Technology, Chennai

---

**Project:** RankFusion-RAG – Secure Document Assistant
