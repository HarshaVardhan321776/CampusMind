export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-[#f8fafc]">
      <header className="bg-white border-b border-[#e2e8f0] px-6 py-4">
        <div className="max-w-3xl mx-auto flex items-center gap-3">
          <a href="/" className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-md bg-[#1a2744] flex items-center justify-center">
              <span className="text-[#B9DDF5] font-serif text-sm font-bold">C</span>
            </div>
            <span className="font-serif font-semibold text-[#1a2744] text-lg">CampusMind</span>
          </a>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-12">
        <h1 className="text-4xl font-serif font-semibold text-[#1a2744] mb-2">Privacy Policy</h1>
        <p className="text-sm text-[#94a3b8] mb-10">Last updated: November 2026</p>

        <div className="prose-cm bg-white border border-[#e2e8f0] rounded-xl p-8 space-y-6 text-[#1e293b]">
          <section>
            <h2>1. Information We Collect</h2>
            <p>We collect the following categories of information:</p>
            <ul>
              <li><strong>Account information:</strong> Name and email address provided during registration</li>
              <li><strong>Uploaded documents:</strong> PDF and DOCX files you choose to upload for AI processing</li>
              <li><strong>Conversation data:</strong> Messages and AI responses within your conversations</li>
              <li><strong>Usage data:</strong> Basic logs of system interactions for performance and debugging</li>
            </ul>
          </section>

          <section>
            <h2>2. How We Use Your Information</h2>
            <p>We use collected information to:</p>
            <ul>
              <li>Provide, operate, and maintain the CampusMind service</li>
              <li>Process your documents and generate AI-assisted responses</li>
              <li>Authenticate your identity and secure your account</li>
              <li>Improve the accuracy and reliability of our AI systems</li>
              <li>Communicate important service updates</li>
            </ul>
          </section>

          <section>
            <h2>3. Document Storage and Processing</h2>
            <p>Documents you upload are stored securely and processed using retrieval-augmented generation (RAG) technology. Document embeddings are stored in a vector database associated with your account. We do not share your documents or their contents with other users. Documents remain available until you explicitly delete them.</p>
          </section>

          <section>
            <h2>4. Data Sharing</h2>
            <p>We do not sell your personal data. We may share limited data with:</p>
            <ul>
              <li><strong>AI providers</strong> (Google Gemini, Groq) for language model inference — governed by their respective privacy policies</li>
              <li><strong>Infrastructure providers</strong> (Vercel, Neon, Pinecone) for hosting and storage — data processed under data processing agreements</li>
              <li><strong>Legal authorities</strong> when required by law or to protect rights and safety</li>
            </ul>
          </section>

          <section>
            <h2>5. Data Security</h2>
            <p>We implement industry-standard security measures including encrypted data transmission (TLS), hashed password storage using bcrypt, JWT-based authentication with token expiration, and access controls limiting data to the authenticated account owner.</p>
          </section>

          <section>
            <h2>6. Data Retention</h2>
            <p>We retain your data for as long as your account is active. Uploaded documents and their embeddings are deleted when you remove them through the interface. You may request complete account deletion by contacting us at support@campusmind.app.</p>
          </section>

          <section>
            <h2>7. Your Rights</h2>
            <p>Depending on your jurisdiction, you may have rights to:</p>
            <ul>
              <li>Access the personal data we hold about you</li>
              <li>Correct inaccurate or incomplete data</li>
              <li>Request deletion of your data</li>
              <li>Export your data in a portable format</li>
              <li>Opt out of certain data processing activities</li>
            </ul>
            <p>To exercise these rights, contact us at <strong>privacy@campusmind.app</strong></p>
          </section>

          <section>
            <h2>8. Cookies and Local Storage</h2>
            <p>CampusMind uses browser local storage to maintain your authentication session (JWT token). We do not use third-party tracking cookies or advertising cookies.</p>
          </section>

          <section>
            <h2>9. Children's Privacy</h2>
            <p>CampusMind is not directed at children under 13. We do not knowingly collect personal information from children under 13. If you believe a child has provided us with personal information, contact us immediately.</p>
          </section>

          <section>
            <h2>10. Changes to This Policy</h2>
            <p>We may update this Privacy Policy periodically. We will notify users of material changes by updating the "Last updated" date and, where appropriate, by email notification. Continued use of the service after changes constitutes acceptance.</p>
          </section>

          <section>
            <h2>11. Contact</h2>
            <p>For privacy inquiries: <strong>privacy@campusmind.app</strong></p>
          </section>
        </div>
      </main>
    </div>
  );
}

