-- Sample SQL script to create documents table and insert sample data
-- Run this on your AWS RDS PostgreSQL database

-- Create documents table
CREATE TABLE IF NOT EXISTS documents (
    id VARCHAR(255) PRIMARY KEY,
    document_id VARCHAR(255) UNIQUE NOT NULL,
    document_content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_documents_document_id ON documents(document_id);

-- Insert sample documents
INSERT INTO documents (id, document_id, document_content, created_at, updated_at)
VALUES 
    (
        'doc-001',
        'doc-001',
        'Machine Learning Fundamentals. Machine learning is a subset of artificial intelligence that enables computers to learn from data without being explicitly programmed. There are three main types: supervised learning where models learn from labeled data, unsupervised learning where models find patterns in unlabeled data, and reinforcement learning where models learn through interaction with an environment. Popular algorithms include decision trees, random forests, support vector machines, and neural networks. Machine learning is widely used in recommendation systems, natural language processing, computer vision, and predictive analytics.',
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    ),
    (
        'doc-002',
        'doc-002',
        'Cloud Computing and AWS. Amazon Web Services (AWS) is a comprehensive cloud computing platform that provides over 200 services including computing, storage, databases, analytics, and machine learning. Key services include EC2 for virtual machines, S3 for object storage, RDS for managed relational databases, and Lambda for serverless computing. AWS follows a shared responsibility model where AWS manages the infrastructure while customers secure their data and applications. The platform is designed for scalability, reliability, and cost-efficiency, making it popular for enterprise applications and startups alike. AWS regions and availability zones provide high availability and disaster recovery capabilities.',
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    ),
    (
        'doc-003',
        'doc-003',
        'Python Programming Best Practices. Python is a versatile programming language known for its readability and ease of use. Best practices include following PEP 8 style guidelines, using virtual environments for project isolation, writing comprehensive unit tests, implementing proper error handling with try-except blocks, and using type hints for better code clarity. Python has a rich ecosystem of libraries for data science (NumPy, Pandas), web development (Django, Flask), and machine learning (TensorFlow, Scikit-learn). Version control with Git and collaborative development practices are essential for team projects. Documentation, comments, and meaningful variable names improve code maintainability and team productivity.',
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    );

-- Verify data
SELECT * FROM documents;
