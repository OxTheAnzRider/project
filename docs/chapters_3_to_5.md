# CHAPTER THREE

# SYSTEM ANALYSIS AND DESIGN

## 3.0 Introduction

This chapter presents the system analysis and design of the proposed Anti-Forgery Proof Certification Registry for Skill Acquisition Using Smart Contracts and Artificial Intelligence. The purpose of the chapter is to translate the problem identified in Chapter One and the research gap identified in Chapter Two into a structured system design that can be implemented, tested, and evaluated. The chapter follows the system analysis and design principles discussed by Dennis, Wixom and Roth in *Systems Analysis and Design with UML*. Their text explains that information systems projects normally pass through planning, analysis, design and implementation phases, and that the analyst must move from business need to requirements, models, architecture, interface, data storage and implementation deliverables. This chapter applies those concepts to the SkillCert system.

The design approach used in this study is object-oriented and prototype-driven. It models the system from the viewpoints of its major actors: learners, issuers, public verifiers, the AI assessment service, the backend application, the IPFS storage layer and the blockchain registry. The design also considers the security and trust assumptions of the system because the goal is not only to build a certificate portal, but to build a certification workflow in which a learner is assessed before certification and the issued certificate can be verified independently after issuance.

In line with the analysis phase described by Dennis, Wixom and Roth, the chapter begins by analysing the existing certification process and its limitations. It then specifies the functional and non-functional requirements of the proposed system, models the system using UML-based descriptions, and presents the architecture, input design, output design, database design, process design and security design of the implemented system.

## 3.1 System Analysis

System analysis is the phase in which the existing situation is studied, problems are identified, requirements are discovered, and the desired behaviour of the new system is defined. Dennis, Wixom and Roth explain that requirements determination is one of the most important activities of the analysis phase because the analyst must understand what users need and convert those needs into clear functional requirements. In this project, the system analysis focuses on how certificates are currently issued, why such certificates are vulnerable to forgery, and how artificial intelligence and blockchain can be combined to improve trust.

### 3.1.1 Analysis of the Existing System

The existing system of certificate issuance in many skill acquisition and academic training environments is largely issuer-centred and document-centred. A learner completes a programme, the issuerevaluates the learner using its internal process, and a paper or digital certificate is issued. Verification is usually performed by visually inspecting the document, contacting the issuing issuer, checking a manually maintained database, or relying on signatures, seals and letterheads.

This approach has several weaknesses. First, the certificate itself is often treated as the main proof of competence, even though the assessment evidence behind it may not be available to employers or third parties. Second, once a certificate is presented outside the issuing issuer, it may be difficult to confirm whether it is authentic, altered, revoked or issued by an authorized officer. Third, where verification depends on manual issueral communication, the process can be slow, inconsistent and difficult to audit. Finally, traditional systems may not provide a strong technical link between learner assessment and certificate issuance. A certificate may therefore appear valid even when the evidence of competence is weak, incomplete or unverifiable.

The existing system can be summarized as follows:

1. Learner attends a skill acquisition or academic programme.
2. issuerevaluates the learner using internal procedures.
3. issuerissues a physical or ordinary digital certificate.
4. Learner presents the certificate to an employer or verifier.
5. Verifier contacts the issueror inspects the certificate manually.
6. issuerconfirms or rejects the certificate if records are available.

This workflow places high trust in the issuing issuerand in the physical or digital document. It does not provide independent cryptographic proof of authenticity, does not provide automated certificate revocation, and does not ensure that assessment evidence is linked to the certificate.

### 3.1.2 Limitations of the Existing System

The limitations of the existing system are:

1. **Certificate forgery and alteration:** Paper certificates and ordinary digital documents can be duplicated, edited or falsely produced.
2. **Slow verification:** Employers and other verifiers may need to contact issuers manually, which delays recruitment and decision-making.
3. **Weak audit trail:** Manual issuance and verification processes do not always record who issued a certificate, when it was issued, what evidence supported it, or whether it has been revoked.
4. **Lack of transparent revocation:** A certificate may remain in circulation even after the issuerwithdraws it.
5. **Separation of assessment and certificate issuance:** Many systems do not technically enforce that the learner must pass a validated assessment before receiving a certificate.
6. **Limited privacy control:** Existing public certificate lists may expose more learner information than necessary.
7. **Centralized trust:** The verifier depends entirely on the issuer's internal database or staff response.
8. **Poor scalability:** Manual verification becomes inefficient as the number of learners, issuers and certificates increases.

These limitations show the need for a system that supports secure learner registration, controlled course enrollment, AI-assisted assessment, automatic certificate issuance after successful assessment, blockchain-based verification, and privacy-preserving public registry statistics.

### 3.1.3 Objectives of the Proposed System

The proposed system is designed to achieve the following objectives:

1. To provide a secure web-based platform for learners and issuers.
2. To enable issuers to create courses and assessment templates.
3. To restrict learner enrollment through issuer-generated course codes.
4. To generate thirty assessment questions from course material using AI-assisted methods.
5. To prevent learners from choosing or manipulating assessment difficulty.
6. To grade learner answers using a hybrid LLM and local rule-based method.
7. To issue certificates only after a learner passes the assessment.
8. To mint certificate NFTs through a smart contract registry.
9. To store certificate metadata and evidence using IPFS where configured.
10. To provide public verification using token ID and verification code.
11. To support certificate revocation while preserving an audit trail.
12. To protect sensitive learner data by exposing only limited public verification information.

## 3.2 System Requirements Specification

The system requirements specification states what the system must do and the quality attributes it must satisfy. In the analysis approach described by Dennis, Wixom and Roth, requirements are derived from user needs, business rules and technical constraints. For this project, requirements were derived from the anti-forgery problem, the needs of learners and issuers, the need for public verification, and the technical properties of AI, blockchain and IPFS.

### 3.2.1 Functional Requirements

The functional requirements are grouped by module.

#### Authentication and User Management

1. The system shall allow learners to register with email, password and wallet address.
2. The system shall allow issuers to register with email, password, issuername and wallet address.
3. The system shall authenticate users through login.
4. The system shall issue access tokens and refresh tokens for authenticated sessions.
5. The system shall protect learner and issuerdashboards from unauthenticated access.
6. The system shall allow logout and session invalidation.

#### Course and Enrollment Management

1. The issuershall create courses with title, description and status.
2. The issuershall generate one or more enrollment codes for a course.
3. The learner shall view available courses without seeing protected course materials.
4. The learner shall enroll in a course by entering a valid issuer-provided code.
5. The backend shall validate code status, expiry and quota before enrollment.
6. The backend shall record learner enrollment date and course relationship.

#### Material and Assessment Template Management

1. The issuershall upload or enter course material.
2. The backend shall send material to the AI service for ingestion.
3. The AI service shall extract key concepts from the material.
4. The issuershall create multiple assessment templates for the same course.
5. Each assessment template shall be linked to a course, material and issuer.
6. Each assessment shall use exactly thirty questions.

#### Assessment Generation

1. The learner shall select an assessment template from an enrolled course.
2. The backend shall confirm learner enrollment before creating an assessment.
3. The backend shall randomly assign or control difficulty without learner selection.
4. The AI service shall attempt to generate questions using OpenAI LLM.
5. The AI service shall validate that generated questions follow the required distribution: eight definition, eight conceptual, seven application and seven analysis questions.
6. The AI service shall fall back to local generation if LLM generation fails, times out or returns invalid JSON.
7. The learner-facing response shall not expose expected answers or rubrics.

#### Answer Submission and Grading

1. The learner shall answer each assessment question.
2. The backend shall store answer submissions.
3. The backend shall send grading requests to the AI service.
4. The AI service shall grade answers locally and semantically where LLM grading is available.
5. The final hybrid score shall prioritize semantic grading while retaining local grading as a consistency signal.
6. The AI service shall return detailed results, feedback, score breakdown, outcome and assessment report hash.
7. The backend shall store assessment result and detailed grading output.

#### Certificate Issuance and Verification

1. The backend shall issue a certificate only if the assessment outcome is PASS.
2. The backend shall generate certificate metadata and a verification code.
3. The backend shall create a certificate PDF.
4. The backend shall pin certificate evidence to IPFS where configured.
5. The backend shall call the smart contract registry to issue the certificate NFT.
6. The system shall store token ID, transaction hash, metadata CID and verification code.
7. Public verifiers shall verify certificates using token ID and verification code.
8. The public registry shall show aggregate statistics without exposing sensitive learner data.
9. Authorized issuers shall be able to revoke certificates.

### 3.2.2 Non-Functional Requirements

#### Security

The system must protect credentials, private keys, learner records and certificate verification codes. JWT authentication is used for protected routes. Passwords are hashed. Environment variables are used for sensitive secrets such as private keys and OpenAI API keys. The blockchain contract enforces authorized issuer permissions before certificates are issued or revoked.

#### Integrity

Assessment records, certificate metadata and blockchain events must preserve evidence of issuance. The assessment report hash is generated deterministically so that the same assessment report produces the same hash. Certificate records are linked to token ID, learner, issuer, assessment and verification code.

#### Privacy

The public verification registry must not expose full learner personal information by default. Learner names and emails are hashed in the local database model, and public verification requires both token ID and verification code before limited certificate details are shown.

#### Availability

The frontend, backend, AI service and blockchain layer should be deployable independently. If the LLM service fails, local assessment fallback allows the system to continue operating.

#### Usability

The interface should support separate learner, issuerand verification workflows. Learners should not be required to understand blockchain details before taking assessments. Issuers should be able to create courses, codes, materials and assessments through the dashboard.

#### Scalability

The system uses a modular architecture. The frontend is static, the backend is API-based, the AI service is separated, and blockchain operations are limited to certificate lifecycle events. This separation makes it easier to scale assessment processing and web requests independently.

#### Maintainability

The codebase is separated into clear modules: frontend scripts, backend API routers, database models, services, AI assessment modules and smart contracts. This follows the design principle of separating responsibilities across system components.

## 3.3 System Design Methodology

The system design methodology adopted for this project is a hybrid of object-oriented analysis and prototyping. Dennis, Wixom and Roth emphasize that systems analysis and design should move through requirements, modelling, architecture design, interface design, data storage design and implementation. This project follows that logic, but applies it in an iterative manner because the system combines several technologies that must be tested together.

The methodology involved the following stages:

1. **Problem identification:** Certificate forgery and weak verification were identified as the central problems.
2. **Requirement determination:** Functional and non-functional requirements were derived from the needs of learners, issuers and verifiers.
3. **Process modelling:** The workflow was decomposed into registration, course creation, enrollment, assessment, grading, certificate issuance and verification.
4. **Object modelling:** System entities such as User, Learner, Issuer, Course, CourseCode, CourseEnrollment, AssessmentTemplate, Assessment and Certificate were identified.
5. **Architecture design:** The system was designed as a modular web, AI and blockchain architecture.
6. **Interface design:** Separate views were created for authentication, learner dashboard, issuerdashboard and public verification.
7. **Data storage design:** Persistent storage was designed for backend records, AI cache and blockchain registry references.
8. **Implementation and testing:** The modules were implemented and tested through local preview, API tests, smart contract tests and end-to-end workflow checks.

### 3.3.1 Justification for Methodology

The object-oriented and prototype-based methodology is suitable for this project because the system has multiple interacting objects and actors. Dennis, Wixom and Roth describe use cases as a way to understand how users interact with a system, and class modelling as a way to represent objects, attributes and relationships. These concepts are directly applicable to SkillCert because the system includes learners, issuers, courses, assessments, certificates and blockchain records.

Prototyping is also appropriate because the research requires practical integration of AI, smart contracts, IPFS and web authentication. The correct behaviour of such a system cannot be fully validated through design diagrams alone. It must be implemented and tested as a working prototype. During development, several issues were discovered and corrected, including frontend route errors, API authentication issues, OpenAI timeout behaviour, ABI mismatch between backend and smart contract, and invalid LLM question distribution. This confirms the importance of iterative prototyping in a multi-component system.

### 3.3.2 Method of Data Collection

The data used for system analysis was collected through:

1. Review of literature on blockchain-based certificate verification, NFTs, smart contracts and AI assessment.
2. Review of the system analysis and design concepts in Dennis, Wixom and Roth.
3. Observation of common certificate issuance and verification workflows.
4. Analysis of the project requirements derived from the research aim and objectives.
5. Testing of the implemented prototype through local issuerand learner workflows.

## 3.4 System Modelling Using UML

UML modelling is used to describe the system in a way that is understandable to developers, stakeholders and evaluators. Dennis, Wixom and Roth explain that analysis models help analysts represent requirements and processes before or during construction. This study applies use case, activity, class and sequence modelling concepts to describe the system.

### 3.4.1 Use Case Model

The major actors are:

1. **Learner:** Registers, logs in, views courses, enrolls with code, takes assessment and views results.
2. **Issuer:** Registers, logs in, creates courses, generates codes, uploads materials, creates assessment templates and monitors learners.
3. **Public verifier:** Views registry statistics and verifies a certificate using token ID and verification code.
4. **AI service:** Ingests material, generates questions, receives answers and grades assessments.
5. **Blockchain registry:** Issues, verifies and revokes NFT certificates.
6. **IPFS service:** Stores certificate metadata and PDF/evidence files.
7. **System administrator:** Manages authorized issuers and deployment configuration.

Main use cases include:

| Actor | Use Case | Description |
|---|---|---|
| Learner | Register/Login | Creates an account and gains access to the learner dashboard. |
| Learner | View Courses | Views available course titles and descriptions. |
| Learner | Enroll in Course | Enters an issuer-provided code to enroll. |
| Learner | Take Assessment | Selects an assessment template and answers questions. |
| Learner | View Result | Views score, outcome, feedback and certificate data. |
| issuer| Create Course | Creates a course record. |
| issuer| Generate Course Code | Generates controlled enrollment codes. |
| issuer| Add Material | Uploads or enters learning material. |
| issuer| Create Template | Creates an assessment template linked to material. |
| issuer| View Learners | Views enrolled learners and assessment results. |
| Public Verifier | Verify Certificate | Checks token ID and verification code. |
| Blockchain Registry | Issue Certificate | Mints/registers certificate NFT after pass. |
| Blockchain Registry | Revoke Certificate | Marks a certificate invalid. |

**Figure 3.1: Use Case Diagram of the Proposed SkillCert System**  
Insert a UML use case diagram showing Learner, Issuer, Public Verifier, AI Service, IPFS and Blockchain Registry actors.

### 3.4.2 Activity Model

The activity flow describes the order of operations from course creation to certificate verification:

1. issuerlogs in.
2. issuercreates course.
3. issuergenerates enrollment code.
4. issueringests material.
5. issuercreates assessment template.
6. Learner logs in.
7. Learner enrolls using code.
8. Learner starts assessment.
9. Backend validates enrollment and template.
10. AI service generates 30 questions.
11. Learner submits answers.
12. AI service grades answers.
13. Backend stores result.
14. If failed, learner sees feedback.
15. If passed, backend generates certificate evidence.
16. Backend calls blockchain registry to issue certificate NFT.
17. Certificate details are stored.
18. Verifier confirms certificate using token ID and verification code.

**Figure 3.2: Activity Diagram for Assessment and Certificate Issuance**  
Insert an activity diagram showing the decision point between PASS, FAIL and PENDING_REVIEW.

### 3.4.3 Class Model

The class model is reflected in the backend SQLAlchemy database models. The main classes are:

| Class | Major Attributes | Relationship |
|---|---|---|
| User | email, password_hash, wallet_address, role | Linked to learner or issuerrole. |
| Learner | did, hashed_name, hashed_email, wallet_address, programme | Has many assessments and certificates. |
| issuer| did, name, wallet_address, accreditation_status | Has courses, materials, assessments and certificates. |
| Course | course_id, title, description, status | Belongs to issuer; has codes, enrollments and templates. |
| CourseCode | code, status, quota, used_count, expires_at | Belongs to course. |
| CourseEnrollment | course_id, learner_id, code_id, enrolled_at | Links learner to course. |
| Material | material_id, content, key_concepts, topics | Belongs to issuer; linked to templates. |
| AssessmentTemplate | assessment_template_id, course_id, material_id, num_questions | Belongs to course and material. |
| Assessment | assessment_id, questions_json, answers_json, ai_score, outcome | Links learner, issuer, course and material. |
| Certificate | token_id, tx_hash, verification_code, metadata_cid, pdf_cid | Linked to learner, issuerand assessment. |
| AuditLog | event_type, actor_did, target_id, detail, tx_hash | Records system events. |
| IssuerKey | issuer_address, private_key_encrypted, revoked_at | Supports issuersigning key management. |

**Figure 3.3: Class Diagram of SkillCert Core Entities**  
Insert a UML class diagram showing User, Learner, Issuer, Course, CourseCode, CourseEnrollment, Material, AssessmentTemplate, Assessment and Certificate.

### 3.4.4 Sequence Model

The most important sequence is assessment-to-certificate issuance:

1. Learner selects an assessment template.
2. Frontend sends `POST /api/assessments/create`.
3. Backend validates learner and enrollment.
4. Backend calls AI service `/create-assessment`.
5. AI service returns learner-safe questions.
6. Learner submits answers using `POST /api/assessments/{id}/answers/submit`.
7. Learner submits grading request.
8. Backend calls AI service `/grade-assessment`.
9. AI service returns score, outcome, feedback and report hash.
10. Backend stores result.
11. If PASS, backend creates metadata and certificate PDF.
12. Backend calls blockchain service.
13. Blockchain service signs and sends transaction to registry contract.
14. Registry mints NFT and emits certificate event.
15. Backend stores certificate token and transaction hash.
16. Frontend displays result.

**Figure 3.4: Sequence Diagram for AI Assessment and NFT Certificate Issuance**

## 3.5 System Design

### 3.5.1 Overall Architecture

The system uses a modular architecture with four main layers:

1. **Presentation layer:** Browser-based frontend built with HTML, CSS and JavaScript.
2. **Application layer:** FastAPI backend handling authentication, courses, assessments, certificates and API orchestration.
3. **AI service layer:** Separate FastAPI microservice handling material ingestion, question generation, grading and report hashing.
4. **Blockchain and storage layer:** Solidity smart contracts on Arbitrum Sepolia and optional IPFS pinning for metadata/PDF evidence.

This architecture follows the architecture design idea described by Dennis, Wixom and Roth, where the analyst must specify how software, hardware, network and security components are arranged to satisfy requirements. The separation of frontend, backend, AI service and blockchain makes the system easier to maintain and test.

**Figure 3.5: System Architecture of SkillCert**  
Insert an architecture diagram showing Frontend, Backend API, Database, AI Service, OpenAI API, IPFS, Arbitrum Sepolia and Smart Contracts.

### 3.5.2 Input Design

Input design focuses on how data enters the system. In the user interface design discussion of Dennis, Wixom and Roth, input validation is important because poor input design can cause wrong data to enter the system. The SkillCert input design includes:

1. **Registration inputs:** email, password, wallet address, role and issuer/learner profile fields.
2. **Course inputs:** title and description.
3. **Course code inputs:** quota and expiry settings.
4. **Material inputs:** title, programme, topics and material content or uploaded file.
5. **Assessment inputs:** assessment template selection and learner answers.
6. **Verification inputs:** token ID and verification code.
7. **Blockchain configuration inputs:** RPC URL, contract addresses and private key stored in `.env`.

Important validation rules include unique email, unique wallet address, valid enrollment code, active assessment template, course enrollment requirement and hidden backend-controlled difficulty.

### 3.5.3 Output Design

The system outputs are:

1. Course lists for learners.
2. Course, code and learner statistics for issuers.
3. Assessment questions.
4. Assessment score, outcome and feedback.
5. Score breakdown showing final, semantic and local scores.
6. Certificate NFT token ID and transaction hash.
7. Certificate PDF.
8. Public registry statistics.
9. Verification response showing valid or invalid certificate status.

The output design follows the principle that outputs should support decision-making. Learners need to know their assessment result; issuers need to monitor courses and learners; verifiers need simple proof of certificate validity.

### 3.5.4 Database Design

The backend database is implemented using SQLAlchemy ORM. During local preview, SQLite is used, but the design can be migrated to PostgreSQL for production. The major tables include users, learners, issuers, courses, course codes, course enrollments, materials, assessment templates, assessments, certificates, audit logs and issuerkeys.

The database design supports referential links among users, courses, assessments and certificates. For example, a certificate links to learner, issuerand assessment. This relationship ensures that a certificate is not an isolated record but part of a traceable evidence chain.

### 3.5.5 Smart Contract Design

The smart contract design contains two contracts:

1. `CertificationNFT.sol`: An ERC721 certificate token contract. It mints SkillCert NFTs and prevents post-mint transfer, making the certificate soulbound.
2. `CertificationRegistry.sol`: A registry contract that authorizes issuers, issues certificates, stores certificate CIDs, verifies certificates and supports revocation.

The registry uses issuer authorization so that only approved addresses can issue or revoke certificates. The verification function returns certificate validity, metadata CID, artefact CID, issuerDID and timestamp. This design provides public verifiability while keeping bulky and sensitive data off-chain.

### 3.5.6 AI Assessment Design

The AI assessment service is designed as a separate microservice. It performs:

1. Material ingestion.
2. Key concept extraction using TF-IDF.
3. LLM-based question generation using OpenAI where available.
4. Local fallback question generation.
5. Answer submission storage.
6. Hybrid grading.
7. Assessment report hashing.

The assessment contains exactly 30 questions: eight definition, eight conceptual, seven application and seven analysis. The expected answers and rubrics are stored internally and not exposed to learners.

### 3.5.7 Security Design

Security is addressed through:

1. Password hashing.
2. JWT authentication and refresh tokens.
3. Role-based dashboard access.
4. Hidden assessment difficulty.
5. Server-side storage of expected answers and rubrics.
6. Verification code requirement for certificate lookup.
7. Smart contract issuer authorization.
8. `.env` protection for API keys and private keys.
9. Public registry aggregation without exposing sensitive learner details.

# CHAPTER FOUR

# SYSTEM IMPLEMENTATION

## 4.0 Introduction

This chapter describes the implementation of the Anti-Forgery Proof Certification Registry for Skill Acquisition Using Smart Contracts and Artificial Intelligence. While Chapter Three described the analysis and design, this chapter explains how the design was converted into a working prototype. It presents the development tools, programming languages, libraries, database implementation, AI implementation, smart contract implementation, frontend implementation, backend implementation, testing and results.

The implementation follows the implementation phase described by Dennis, Wixom and Roth, where the system is constructed, tested and prepared for use. In this project, implementation required combining web development, API development, AI service integration, blockchain smart contracts and local preview testing.

## 4.1 Development Environment and Tools

The system was developed as a multi-service application. The main development environment and tools are:

| Component | Tool/Technology | Purpose |
|---|---|---|
| Frontend | HTML, CSS, JavaScript | Browser interface for users. |
| Backend | Python FastAPI | API, database, authentication and orchestration. |
| AI Service | Python FastAPI | AI assessment generation and grading. |
| Database | SQLite locally, SQLAlchemy ORM | Persistent storage. |
| Smart Contracts | Solidity | NFT certificate and registry contracts. |
| Contract Framework | Foundry | Contract build and testing. |
| Blockchain | Arbitrum Sepolia | Testnet deployment and certificate issuance. |
| AI API | OpenAI `gpt-4o-mini` | Semantic question generation and grading. |
| Storage | IPFS/Pinata where configured | Metadata and certificate evidence. |
| Version Control | Git | Source code management. |

### 4.1.1 Programming Languages and Libraries

The frontend uses HTML, CSS and JavaScript. The backend and AI service use Python. The contracts use Solidity version `0.8.20`.

Important backend libraries include:

1. FastAPI for API routing.
2. SQLAlchemy for ORM database models.
3. Pydantic for request and response validation.
4. HTTPX for service-to-service requests.
5. Web3.py for blockchain communication.
6. JWT and password hashing utilities for authentication.
7. FPDF/qrcode-related utilities for certificate PDF generation where configured.

Important AI service libraries include:

1. scikit-learn for TF-IDF and local similarity scoring.
2. OpenAI Python SDK for LLM calls.
3. Pydantic for strict validation of LLM JSON.
4. SQLite persistence for AI service cache.
5. hashlib/json for deterministic assessment report hashing.

Important contract libraries include OpenZeppelin ERC721 and AccessControl components.

### 4.1.2 Development Platform and Hardware Requirements

The system was developed and previewed locally on a Linux-based environment. The minimum hardware requirements for local testing are:

1. Dual-core processor or better.
2. At least 4GB RAM.
3. Stable internet connection for OpenAI API, Arbitrum Sepolia RPC and IPFS pinning.
4. A modern browser such as Chrome.
5. Python virtual environments for backend and AI service.
6. Foundry installed for Solidity testing.

## 4.2 Dataset Description and Preprocessing

The prototype does not depend on a fixed public dataset. Instead, the issuerprovides learning material for each course. The AI service ingests this material and uses it as the basis for question generation and grading.

The preprocessing steps include:

1. Receiving material title, programme and content.
2. Storing material in the backend database.
3. Sending material to the AI service.
4. Extracting key concepts using TF-IDF.
5. Storing material and key concepts in the AI service persistence layer.
6. Using the material text and key concepts as input to the question generation process.

The design is suitable for skill acquisition because different issuers can provide different materials for different courses. Each assessment template can therefore be generated from the material relevant to that course.

## 4.3 Model Architecture and Methodology

The AI model methodology is hybrid. It combines local rule-based/TF-IDF processing with LLM-based semantic generation and grading.

### 4.3.1 Question Generation Method

The system first extracts key concepts from the material. It then attempts LLM question generation. The LLM is instructed to return strict JSON. The response must contain exactly thirty questions with the following distribution:

1. Eight definition questions.
2. Eight conceptual questions.
3. Seven application questions.
4. Seven analysis questions.

Each internal question includes:

1. question ID.
2. question text.
3. expected answer.
4. question type.
5. backend-controlled difficulty.
6. key concepts.
7. rubric.
8. points.

However, expected answers and rubrics are removed from learner-facing responses. This prevents learners from seeing the answers before submission.

### 4.3.2 Local Fallback Method

If OpenAI is unavailable, times out or returns invalid JSON, the AI service falls back to local question generation. This makes the system more resilient because assessments can still be created even when the LLM service is unavailable.

### 4.3.3 Hybrid Grading Method

The grading process works as follows:

1. Local grading runs for each answer.
2. LLM semantic grading runs in batch where OpenAI is available.
3. If LLM grading succeeds, the final score uses 85 percent LLM score and 15 percent local score.
4. If LLM grading fails, local grading is used fully.
5. The system returns final score, semantic score, local score, feedback and consistency notes.

The local grader uses:

1. TF-IDF cosine similarity.
2. Keyword overlap.
3. Completeness based on answer length.
4. Question-type rubrics for definition, conceptual, application and analysis questions.

The LLM grader uses the question, expected answer, rubric and student answer. This improves fairness because learners may express correct answers using wording that differs from the course material.

### 4.3.4 Competency and Anomaly Detection

The codebase supports optional Random Forest competency classification and Isolation Forest anomaly detection. The model service checks for model artifacts:

1. `competency_model.joblib`
2. `anomaly_model.joblib`
3. `scaler.joblib`
4. `feature_names.json`

If the artifacts are missing or incompatible, the system logs a warning and continues without crashing. During the current prototype preview, these artifacts are not present, so competency and anomaly checks are disabled. The design still preserves the extension point for future trained-model integration.

### 4.3.5 Assessment Report Hash

After grading, the AI service generates an assessment report hash. The hash is produced from deterministic JSON using SHA-256. The purpose is to create a stable evidence reference that can later be included in certificate metadata or pinned to IPFS.

## 4.4 System Implementation and Modules

### 4.4.1 Frontend Module

The frontend is located in `frontend/public`. It provides pages and scripts for:

1. Authentication.
2. Learner dashboard.
3. issuerdashboard.
4. Public verification dashboard.

The learner dashboard allows learners to view available courses, enroll with a code, start assessments, answer questions and view results. The issuerdashboard allows issuers to create courses, generate codes, add materials, create assessment templates and monitor learners. The verification dashboard allows public certificate checks.

### 4.4.2 Backend Module

The backend is located in `backend/app`. It is implemented with FastAPI and SQLAlchemy. The major API modules include:

1. `auth.py` for registration, login, refresh token, logout and password recovery endpoints.
2. `courses.py` for course listing, enrollment and learner course retrieval.
3. `issuers.py` for course creation, code generation, material upload, template creation and learner result export.
4. `assessments.py` for material ingestion, assessment creation, answer submission, grading and result retrieval.
5. `certificates.py` for registry statistics, verification, revocation and learner certificate lookup.

The backend also contains services for blockchain calls, IPFS pinning, certificate PDF generation and issuerkey management.

### 4.4.3 AI Service Module

The AI service is located in `ai_service/app`. Its major files include:

1. `main.py`: FastAPI endpoints.
2. `assessment.py`: material store, question generation, answer submission and grading engine.
3. `llm_service.py`: OpenAI integration and strict JSON validation.
4. `model_service.py`: optional competency and anomaly model loading.
5. `persistence.py`: SQLite persistence for AI cache.
6. `hash_utils.py`: deterministic assessment report hashing.

The AI service runs independently on port `8001`.

### 4.4.4 Smart Contract Module

The contracts are located in `contracts/src`.

`CertificationNFT.sol` implements the SkillCert NFT. It uses ERC721 URI storage and restricts minting to the registry contract. It also prevents transfer after minting, making the certificate non-transferable.

`CertificationRegistry.sol` manages issuer authorization, certificate issuance, verification and revocation. It stores certificate metadata CID, assessment artefact CID, issuerDID and issuance timestamp.

### 4.4.5 Blockchain Service Module

The backend blockchain service uses Web3.py to connect to Arbitrum Sepolia. It loads the registry contract ABI and signs certificate issuance transactions. It supports issuer authorization checks, certificate issuance, verification and revocation.

### 4.4.6 Certificate PDF and Verification Module

When a learner passes an assessment, the backend generates certificate metadata and a PDF certificate. The PDF includes learner wallet, issuer, course, assessment, score, NFT token ID and verification code. The verification dashboard requires token ID and verification code before showing certificate validity.

## 4.5 Testing and Evaluation

Testing was carried out at different levels.

### 4.5.1 Smart Contract Testing

Foundry tests were written for the smart contracts. The tests cover:

1. Admin authorizing issuers.
2. Authorized issuer issuing a certificate.
3. Unauthorized issuer being prevented from issuing a certificate.
4. Authorized issuer revoking a certificate.
5. Soulbound NFT transfer prevention.

The tests passed after synchronizing the smart contract ABI and backend blockchain service.

### 4.5.2 API and Integration Testing

The backend and AI services were tested through local API calls. Confirmed checks include:

1. AI health endpoint showing OpenAI key configured.
2. OpenAI model reachability for `gpt-4o-mini`.
3. Real LLM question generation producing exactly thirty questions.
4. Backend health connecting to Arbitrum Sepolia.
5. Course creation and enrollment through API.
6. Assessment creation after enrollment.

### 4.5.3 Frontend Testing

The frontend was tested locally through:

1. issuerregistration and login.
2. Course creation.
3. Code generation.
4. Material ingestion.
5. Assessment template creation.
6. Learner registration and enrollment.
7. Assessment start and question display.
8. Result display.
9. Verification dashboard access.

### 4.5.4 Error Handling and Debugging

Several development issues were identified and fixed:

1. Frontend `switchTab` reference error.
2. Wrong dashboard redirection after login.
3. Unauthorized course creation caused by stale or missing tokens.
4. Course enrollment fetch error caused by service/API availability.
5. Incorrect verification statistics caused by counting course codes incorrectly.
6. Backend AI request timeout during 30-question LLM generation.
7. OpenAI API key not visible to AI service.
8. LLM returning invalid question distribution.
9. Backend `DEBUG=release` parsing crash.
10. Smart contract ABI mismatch.
11. Foundry private key missing `0x` prefix.
12. Real secret accidentally appearing in an example env file.

These issues were important because they tested the reliability of the architecture and forced the implementation to become more robust.

## 4.6 Results Presentation and Analysis

### 4.6.1 Output Samples and Interface Screens

The following screenshots should be inserted:

1. **Figure 4.1:** Authentication page.
2. **Figure 4.2:** issuerdashboard.
3. **Figure 4.3:** Course creation form.
4. **Figure 4.4:** Course code generation output.
5. **Figure 4.5:** Learner dashboard showing available courses.
6. **Figure 4.6:** Assessment question screen.
7. **Figure 4.7:** Assessment result and feedback screen.
8. **Figure 4.8:** Public verification dashboard.
9. **Figure 4.9:** Smart contract test output.

### 4.6.2 Discussion of Results and System Performance

The implemented prototype satisfies the main research objectives. It provides a working system where learners and issuers can register, issuers can create courses and assessment templates, learners can enroll using codes, assessments can be generated using AI, and certificates can be issued through blockchain after successful assessment.

The AI service successfully generated an assessment using OpenAI with the required distribution of 30 questions. The backend successfully connected to Arbitrum Sepolia with chain ID `421614`. The smart contract test suite passed, confirming that issuer authorization, certificate issuance, revocation and transfer restriction work as expected.

The system also demonstrates resilience. If the LLM fails or returns invalid output, local fallback prevents assessment generation from collapsing. If competency and anomaly artifacts are unavailable, the system logs the issue and continues grading without crashing. If certificate issuance fails after grading, the backend records the assessment result and reports certificate issuance failure instead of losing the assessment record.

The major limitation observed during testing was the time required for LLM generation of thirty structured questions. This was addressed by increasing backend AI timeout and adding longer OpenAI timeout configuration. Another limitation is that trained competency and anomaly models are not currently active because their artifacts are missing. This does not prevent the prototype from functioning, but future work should include training and validating those models with representative assessment data.

# CHAPTER FIVE

# SUMMARY, RECOMMENDATIONS AND CONCLUSION

## 5.1 Introduction

This chapter presents the summary, conclusion and recommendations of the study. The research focused on the design and implementation of an anti-forgery proof certification registry for skill acquisition using smart contracts and artificial intelligence. The system was developed to address certificate forgery, weak verification, lack of transparent revocation and the absence of a strong technical link between learner assessment and certificate issuance.

## 5.2 Summary

The study began by identifying certificate forgery as a major challenge in skill acquisition and academic environments. Existing systems often rely on paper certificates, ordinary digital documents or manual issueral verification. Such systems are vulnerable to alteration, duplication, slow verification and weak auditability.

The literature review showed that blockchain can provide immutability, provenance and public verification, while smart contracts can automate certificate issuance and revocation. It also showed that NFTs can represent unique credentials, but privacy must be protected by keeping sensitive data off-chain. The review further showed that AI can support learner assessment, but many existing systems do not connect AI evaluation directly to blockchain certificate issuance.

To address these gaps, this study designed and implemented SkillCert, a modular system consisting of a frontend, backend API, AI assessment service and smart contract registry. The frontend provides learner, issuerand public verifier interfaces. The backend manages authentication, courses, enrollments, assessments, certificates and blockchain orchestration. The AI service generates and grades assessments using a hybrid LLM and local grading method. The smart contracts issue, verify and revoke soulbound NFT certificates.

The system implements course enrollment using issuer-generated codes, multiple assessments per course, backend-controlled assessment difficulty, exactly thirty questions per assessment, hybrid AI grading, certificate PDF generation, verification code-based public verification and blockchain-backed certificate records.

Testing confirmed that the AI service can generate valid thirty-question assessments, the backend can communicate with the AI service and blockchain, the frontend can support the main workflows, and the smart contracts can enforce issuer authorization and certificate revocation.

## 5.3 Conclusion

This study concludes that integrating artificial intelligence with blockchain smart contracts can improve the trustworthiness of skill acquisition certification. The AI component strengthens the pre-issuance stage by evaluating learner performance before a certificate is issued. The blockchain component strengthens the post-issuance stage by providing a tamper-resistant registry where certificate authenticity can be independently verified.

The proposed system reduces the possibility of forged certificates because certificates are not merely uploaded as documents; they are linked to assessment records, verification codes, metadata references and NFT token IDs. The use of smart contracts also ensures that only authorized issuers can issue or revoke certificates. Public verification improves transparency, while privacy is protected by limiting the data exposed in the public registry.

Although the system is a prototype, it demonstrates a practical path toward secure, verifiable and assessment-backed certification. It also shows that a modular architecture is suitable for this type of project because the frontend, backend, AI service and blockchain contracts can be developed and tested independently.

The project therefore achieves its main aim: to implement an anti-forgery proof certification registry for skill acquisition using smart contracts and artificial intelligence.

## 5.4 Recommendations

Based on the implementation and testing, the following recommendations are made:

1. Issuers should adopt verification systems that link certificates to assessment evidence rather than issuing certificates as isolated documents.
2. Future versions should train and validate the Random Forest competency model and Isolation Forest anomaly model using representative learner assessment data.
3. The system should be tested with real issuers and learners to evaluate usability, accuracy and operational readiness.
4. Additional privacy-preserving methods such as selective disclosure or zero-knowledge proofs should be explored.
5. The IPFS pinning workflow should be strengthened for production by using reliable pinning services and retention policies.
6. The certificate verification registry should be extended with issueraccreditation checks.
7. The AI grading method should continue to be audited for fairness, especially across different writing styles and skill domains.
8. Future work should add richer practical-skill evidence such as supervisor attestations, images, video records or practical task rubrics.
9. Production deployment should use a stronger database such as PostgreSQL and a secure key-management system.
10. A formal appeal and human review workflow should be introduced for borderline or anomalous assessment results.
11. Issuers should receive training on private key safety, course material quality and responsible AI-assisted assessment.
12. The system should be integrated with national or issueral education policies before large-scale deployment.

## 5.5 Contribution to Knowledge

The contribution of this project is the integration of three important ideas into one working prototype:

1. AI-based learner assessment before certificate issuance.
2. NFT-based certificate representation through smart contracts.
3. Public verification using blockchain records and verification codes.

Unlike systems that focus only on certificate storage or only on AI assessment, this project connects learner evaluation directly to credential issuance. This helps reduce the "garbage in, garbage out" weakness of blockchain credential systems by ensuring that certificate minting depends on assessment outcome rather than manual document upload alone.

## 5.6 Areas for Further Study

Further study may focus on:

1. Training AI competency models with larger domain-specific datasets.
2. Evaluating the grading accuracy of LLM-assisted assessment across multiple skill areas.
3. Studying the legal acceptance of NFT certificates in Nigerian issuers.
4. Comparing Arbitrum Sepolia or Arbitrum mainnet with other blockchain networks for cost and performance.
5. Implementing decentralized identity standards for learners and issuers.
6. Adding zero-knowledge proof verification to reduce public data exposure.
7. Studying employer adoption and trust in blockchain-backed certificates.

## References

Achour, M., et al. (2025). Studies on artificial intelligence assessment, fairness and human-centred evaluation.

Balducci, F. (2024). Artificial intelligence tools and explainability in learner assessment.

Delgado-von-Eitzen, C. (2024). NFTs in education and GDPR compliance.

Dennis, A., Wixom, B. H., & Roth, R. M. (2012). *Systems Analysis and Design with UML* (5th ed.). John Wiley & Sons.

Frisch, R. (2023). Blockchain diploma authenticity verification system using smart contract.

Ifeyemi, Oyedeji, & Adebiyi. (2024). A blockchain-based digital educational certificate verification system in Nigeria.

Kulkarni, Toksha, & Gupta. (2022). AI and machine learning methods for educational assessment.

Lone, A. H. (2020). Forgery protection of academic certificates through integrity preservation at scale using Ethereum smart contracts.

Owan, V. J. (2025). Artificial intelligence and educational assessment systems.

Zhang. Immutable digital recognition via blockchain.

