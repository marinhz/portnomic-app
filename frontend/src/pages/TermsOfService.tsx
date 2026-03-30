const TERMS_OF_SERVICE_TEXT = `Terms of Service
Last Updated: March 30, 2026

Welcome to Portnomic. These Terms of Service ("Terms") govern your access to and use of the Portnomic platform, including the Sentinel™ AI Audit Engine (collectively, the "Service"). By using our Service, you agree to be bound by these Terms.

1. Description of Service
Portnomic provides an AI-driven auditing platform designed for the maritime industry to verify port call expenses, Disbursement Accounts (DAs), and operational logs (SOF). The Service includes data extraction, automated discrepancy detection, and financial reporting.

2. Google API & Data Access
Our Service may request access to your Google Account (e.g., Gmail or Google Drive) to automate the retrieval of maritime documents such as invoices and Statements of Facts.

Purpose: Access is used exclusively to identify and audit port-related financial documents.

Strict Use: Portnomic complies with the Google API Services User Data Policy, including Limited Use requirements. We do not use your data for advertising or sell it to third parties.

3. User Responsibilities
You are responsible for:

Maintaining the confidentiality of your account credentials.

Ensuring that the documents provided for audit are authentic.

Reviewing the AI-generated findings. Portnomic provides analytical tools, but final financial decisions remain with the user.

4. Intellectual Property
All content, software, and the Sentinel™ AI logic are the exclusive property of Portnomic. You are granted a limited, non-exclusive license to use the Service for your professional maritime operations.

5. Limitation of Liability
Portnomic is provided "as is." While our AI strives for maximum accuracy, we do not guarantee that the Service will be error-free. Portnomic shall not be liable for any financial losses, missed discounts, or operational delays resulting from the use of the platform.

6. Termination
You may stop using the Service at any time by disconnecting your Google Account through your Portnomic settings or Google’s security portal. Portnomic reserves the right to suspend accounts that violate these Terms.

7. Governing Law
These Terms are governed by the laws of the Republic of Bulgaria.

8. Contact Us
For questions regarding these Terms, please contact us at: contact@portnomic.com
`;

export function TermsOfServicePage() {
  return (
    <div className="flex min-h-screen items-start justify-center bg-gradient-to-br from-navy-950 via-navy-800 to-navy-700 px-4 py-10">
      <div className="w-full max-w-3xl rounded-xl bg-white p-7 shadow-2xl dark:bg-navy-950">
        <pre className="whitespace-pre-wrap font-sans leading-relaxed text-slate-800 dark:text-slate-100">
          {TERMS_OF_SERVICE_TEXT}
        </pre>
      </div>
    </div>
  );
}

