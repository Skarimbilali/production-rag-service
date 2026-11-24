
"use strict";

const API_BASE_URL = "http://127.0.0.1:8000";

const elements = {
    apiStatus: document.getElementById("apiStatus"),

    uploadForm: document.getElementById("uploadForm"),
    documentFile: document.getElementById("documentFile"),
    uploadButton: document.getElementById("uploadButton"),
    uploadMessage: document.getElementById("uploadMessage"),

    documentsList: document.getElementById("documentsList"),
    refreshDocuments: document.getElementById("refreshDocuments"),

    questionForm: document.getElementById("questionForm"),
    questionInput: document.getElementById("questionInput"),
    topK: document.getElementById("topK"),
    threshold: document.getElementById("threshold"),
    askButton: document.getElementById("askButton"),
    questionMessage: document.getElementById("questionMessage"),

    answerBox: document.getElementById("answerBox"),
    citationsList: document.getElementById("citationsList"),

    retrievedChunks: document.getElementById("retrievedChunks"),
    retrievedCount: document.getElementById("retrievedCount")
};


// --------------------------------------------------
// Helpers
// --------------------------------------------------

function showMessage(element, message, isError = false) {
    element.textContent = message;

    element.classList.remove(
        "message-success",
        "message-error"
    );

    element.classList.add(
        isError ? "message-error" : "message-success"
    );
}


function createElement(tag, text = "", className = "") {
    const element = document.createElement(tag);

    element.textContent = String(text);

    if (className) {
        element.className = className;
    }

    return element;
}


async function apiRequest(endpoint, options = {}) {
    let response;

    try {
        response = await fetch(
            `${API_BASE_URL}${endpoint}`,
            options
        );
    } catch {
        throw new Error(
            "Cannot connect to FastAPI. Check that the server is running."
        );
    }

    let result = null;

    if (response.status !== 204) {
        const contentType =
            response.headers.get("content-type") || "";

        if (contentType.includes("application/json")) {
            result = await response.json();
        } else {
            result = await response.text();
        }
    }

    if (!response.ok) {
        let errorMessage = `Request failed (${response.status}).`;

        if (result && typeof result === "object") {
            if (typeof result.detail === "string") {
                errorMessage = result.detail;
            } else if (Array.isArray(result.detail)) {
                errorMessage = result.detail
                    .map(item => item.msg || "Validation error")
                    .join("; ");
            }
        }

        throw new Error(errorMessage);
    }

    return result;
}


// --------------------------------------------------
// API Health
// --------------------------------------------------

async function checkApiHealth() {
    elements.apiStatus.textContent = "Checking API...";

    elements.apiStatus.classList.remove(
        "online",
        "offline"
    );

    try {
        await apiRequest("/health");

        elements.apiStatus.textContent = "API Online";
        elements.apiStatus.classList.add("online");

    } catch {
        elements.apiStatus.textContent = "API Offline";
        elements.apiStatus.classList.add("offline");
    }
}


// --------------------------------------------------
// Document Upload
// --------------------------------------------------

async function uploadDocument(event) {
    event.preventDefault();

    const file = elements.documentFile.files[0];

    if (!file) {
        showMessage(
            elements.uploadMessage,
            "Please select a PDF or DOCX file.",
            true
        );
        return;
    }

    const extension = file.name
        .split(".")
        .pop()
        .toLowerCase();

    if (!["pdf", "docx"].includes(extension)) {
        showMessage(
            elements.uploadMessage,
            "Only PDF and DOCX files are supported.",
            true
        );
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    elements.uploadButton.disabled = true;

    showMessage(
        elements.uploadMessage,
        "Uploading and processing document..."
    );

    try {
        await apiRequest("/documents/upload", {
            method: "POST",
            body: formData
        });

        showMessage(
            elements.uploadMessage,
            "Document uploaded successfully."
        );

        elements.uploadForm.reset();

        await loadDocuments();

    } catch (error) {
        showMessage(
            elements.uploadMessage,
            error.message,
            true
        );

    } finally {
        elements.uploadButton.disabled = false;
    }
}


// --------------------------------------------------
// Documents List
// --------------------------------------------------

function normalizeDocuments(result) {
    if (Array.isArray(result)) {
        return result;
    }

    if (result && Array.isArray(result.documents)) {
        return result.documents;
    }

    return [];
}


async function loadDocuments() {
    elements.documentsList.replaceChildren(
        createElement("p", "Loading documents...")
    );

    try {
        const result = await apiRequest("/documents");

        const documents = normalizeDocuments(result);

        elements.documentsList.replaceChildren();

        if (documents.length === 0) {
            elements.documentsList.appendChild(
                createElement("p", "No documents uploaded yet.")
            );
            return;
        }

        documents.forEach(documentItem => {
            const documentId =
                documentItem.document_id || documentItem.id;

            const filename =
                documentItem.filename ||
                documentItem.name ||
                "Unknown document";

            const card = createElement(
                "div",
                "",
                "document-item"
            );

            card.appendChild(
                createElement("strong", filename)
            );

            const chunksCount =
                documentItem.chunk_count ??
                documentItem.chunks_count ??
                documentItem.total_chunks;

            if (chunksCount !== undefined) {
                card.appendChild(
                    createElement(
                        "p",
                        `Chunks: ${chunksCount}`
                    )
                );
            }

            if (documentId) {
                const deleteButton = createElement(
                    "button",
                    "Delete Document"
                );

                deleteButton.type = "button";

                deleteButton.addEventListener(
                    "click",
                    () => deleteDocument(
                        documentId,
                        filename
                    )
                );

                card.appendChild(deleteButton);
            }

            elements.documentsList.appendChild(card);
        });

    } catch (error) {
        elements.documentsList.replaceChildren(
            createElement("p", error.message)
        );
    }
}


// --------------------------------------------------
// Document Delete
// --------------------------------------------------

async function deleteDocument(documentId, filename) {
    const confirmed = window.confirm(
        `Delete "${filename}" and its stored chunks?`
    );

    if (!confirmed) {
        return;
    }

    try {
        await apiRequest(
            `/documents/${encodeURIComponent(documentId)}`,
            {
                method: "DELETE"
            }
        );

        showMessage(
            elements.uploadMessage,
            "Document deleted successfully."
        );

        await loadDocuments();

    } catch (error) {
        showMessage(
            elements.uploadMessage,
            error.message,
            true
        );
    }
}


// --------------------------------------------------
// Ask Question
// --------------------------------------------------

async function askQuestion(event) {
    event.preventDefault();

    const question =
        elements.questionInput.value.trim();

    if (!question) {
        showMessage(
            elements.questionMessage,
            "Please enter a question.",
            true
        );
        return;
    }

    const payload = {
        question: question,
        top_k: Number(elements.topK.value),
        threshold: Number(elements.threshold.value)
    };

    elements.askButton.disabled = true;

    elements.answerBox.textContent =
        "Generating answer...";

    elements.citationsList.replaceChildren();
    elements.retrievedChunks.replaceChildren();

    elements.retrievedCount.textContent = "0 chunks";

    showMessage(
        elements.questionMessage,
        "Retrieving relevant document chunks..."
    );

    try {
        const result = await apiRequest(
            "/questions/ask",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            }
        );

        elements.answerBox.textContent =
            result.answer || "No answer returned.";

        renderCitations(result.citations || []);

        renderRetrievedChunks(
            result.retrieved_chunks || [],
            result.retrieved_count
        );

        showMessage(
            elements.questionMessage,
            "Question processed successfully."
        );

    } catch (error) {
        elements.answerBox.textContent =
            "Unable to generate an answer.";

        showMessage(
            elements.questionMessage,
            error.message,
            true
        );

    } finally {
        elements.askButton.disabled = false;
    }
}


// --------------------------------------------------
// Source Citations
// --------------------------------------------------

function renderCitations(citations) {
    elements.citationsList.replaceChildren();

    if (citations.length === 0) {
        elements.citationsList.appendChild(
            createElement("p", "No citations available.")
        );
        return;
    }

    citations.forEach(citation => {
        const metadata = citation.metadata || {};

        const card = createElement(
            "div",
            "",
            "citation-item"
        );

        card.appendChild(
            createElement(
                "strong",
                `Source: ${citation.source_id}`
            )
        );

        card.appendChild(
            createElement(
                "p",
                `File: ${metadata.filename || "Unknown"}`
            )
        );

        card.appendChild(
            createElement(
                "p",
                `Page: ${metadata.page ?? "N/A"}`
            )
        );

        card.appendChild(
            createElement(
                "p",
                `Chunk ID: ${citation.chunk_id}`
            )
        );

        elements.citationsList.appendChild(card);
    });
}


// --------------------------------------------------
// Retrieved Chunks
// --------------------------------------------------

function renderRetrievedChunks(chunks, retrievedCount) {
    elements.retrievedChunks.replaceChildren();

    const count = retrievedCount ?? chunks.length;

    elements.retrievedCount.textContent =
        `${count} chunks`;

    if (chunks.length === 0) {
        elements.retrievedChunks.appendChild(
            createElement(
                "p",
                "No relevant document chunks found."
            )
        );
        return;
    }

    chunks.forEach((chunk, index) => {
        const metadata = chunk.metadata || {};

        const card = createElement(
            "div",
            "",
            "chunk-item"
        );

        card.appendChild(
            createElement(
                "strong",
                `Chunk ${index + 1}`
            )
        );

        const score = Number(
            chunk.similarity_score
        );

        if (Number.isFinite(score)) {
            card.appendChild(
                createElement(
                    "span",
                    `Similarity: ${(score * 100).toFixed(2)}%`,
                    "score"
                )
            );
        }

        card.appendChild(
            createElement(
                "p",
                `File: ${metadata.filename || "Unknown"} | Page: ${metadata.page ?? "N/A"}`,
                "chunk-meta"
            )
        );

        card.appendChild(
            createElement(
                "p",
                chunk.text || "No text available.",
                "chunk-text"
            )
        );

        elements.retrievedChunks.appendChild(card);
    });
}


// --------------------------------------------------
// Event Listeners
// --------------------------------------------------

elements.uploadForm.addEventListener(
    "submit",
    uploadDocument
);

elements.questionForm.addEventListener(
    "submit",
    askQuestion
);

elements.refreshDocuments.addEventListener(
    "click",
    loadDocuments
);


// --------------------------------------------------
// Application Initialization
// --------------------------------------------------

async function initializeApp() {
    await checkApiHealth();
    await loadDocuments();
}

initializeApp();
