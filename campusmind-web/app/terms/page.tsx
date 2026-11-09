export default function TermsPage() {
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
        <h1 className="text-4xl font-serif font-semibold text-[#1a2744] mb-2">Terms of Service</h1>
        <p className="text-sm text-[#94a3b8] mb-10">Last updated: November 2026</p>

        <div className="prose-cm bg-white border border-[#e2e8f0] rounded-xl p-8 space-y-6 text-[#1e293b]">
          <section>
            <h2>1. Acceptance of Terms</h2>
            <p>By accessing and using CampusMind, you accept and agree to be bound by these Terms of Service. If you do not agree to these terms, do not use the service.</p>
          </section>

          <section>
            <h2>2. Description of Service</h2>
            <p>CampusMind is an AI-powered academic assistant that enables users to upload documents, engage in AI-assisted conversations, and retrieve knowledge from their uploaded materials. The service uses large language models and retrieval-augmented generation technology.</p>
          </section>

          <section>
            <h2>3. User Accounts</h2>
            <p>You are responsible for maintaining the confidentiality of your account credentials. You agree to provide accurate and current information during registration. You may not share your account with others or use another person's account.</p>
          </section>

          <section>
            <h2>4. Acceptable Use</h2>
            <p>You agree not to use CampusMind to:</p>
            <ul>
              <li>Upload content that is illegal, harmful, or violates intellectual property rights</li>
              <li>Submit misleading, fraudulent, or deceptive information</li>
              <li>Attempt to access other users' data or compromise system security</li>
              <li>Use the service for academic dishonesty or plagiarism</li>
              <li>Reverse-engineer, decompile, or disassemble any part of the service</li>
            </ul>
          </section>

          <section>
            <h2>5. Uploaded Content</h2>
            <p>You retain ownership of documents you upload. By uploading, you grant CampusMind a limited license to process and analyze your documents solely to provide the service. We do not share your uploaded documents with other users or third parties.</p>
          </section>

          <section>
            <h2>6. AI-Generated Content</h2>
            <p>CampusMind uses AI models to generate responses. AI-generated content may contain inaccuracies, errors, or outdated information. You should not rely solely on AI responses for critical academic, legal, medical, or financial decisions. Always verify important information with authoritative sources.</p>
          </section>

          <section>
            <h2>7. Data and Privacy</h2>
            <p>Your use of CampusMind is also governed by our Privacy Policy, which is incorporated into these Terms. We handle your data in accordance with applicable privacy laws.</p>
          </section>

          <section>
            <h2>8. Service Availability</h2>
            <p>CampusMind is provided on an "as-is" and "as-available" basis. We do not guarantee uninterrupted, error-free operation. We may suspend or terminate the service at any time for maintenance, updates, or other operational reasons.</p>
          </section>

          <section>
            <h2>9. Limitation of Liability</h2>
            <p>To the maximum extent permitted by applicable law, CampusMind and its operators shall not be liable for any indirect, incidental, special, consequential, or punitive damages, including loss of data or academic opportunity, arising from your use of the service.</p>
          </section>

          <section>
            <h2>10. Changes to Terms</h2>
            <p>We may update these Terms of Service periodically. Continued use of the service after changes constitutes acceptance of the revised terms. We will notify users of significant changes via email or in-application notice.</p>
          </section>

          <section>
            <h2>11. Contact</h2>
            <p>For questions about these Terms of Service, contact us at: <strong>support@campusmind.app</strong></p>
          </section>
        </div>
      </main>
    </div>
  );
}

