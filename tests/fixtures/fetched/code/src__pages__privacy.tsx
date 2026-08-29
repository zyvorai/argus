// Copyright (c) 2026 ZyvorAI Labs Private Limited. All rights reserved.
// Proprietary software — see LICENSE in the repository root.
// https://zyvor.dev · info@zyvor.dev

import type {ReactNode} from 'react';
import {EMAIL_INFO} from '../data/emails';
import {LEGAL_ENTITY_INDIA} from '../data/legal-entity-india';
import {ProductPage, PageContent, SectionHeader, FeatureGrid, styles, MarketingHero} from '../components/shared';

export default function Privacy(): ReactNode {
  return (
    <ProductPage
      title="Privacy Policy"
      description="Zyvor Privacy Policy — how we collect, use, and protect your data when you use the HyperSDK Platform."
    >
      <MarketingHero pageId="privacy" />

      <PageContent>
        {/* Privacy at a Glance */}
        <SectionHeader
          eyebrow="At a Glance"
          title="Privacy at a Glance"
          subtitle="The short version of our privacy practices."
        />
        <FeatureGrid
          columns={2}
          features={[
            {
              title: 'We Collect',
              desc: 'Account information, usage data, and VM metadata (job status, sizes, formats). We never access or store the contents of your virtual machine disks.',
            },
            {
              title: 'We Never',
              desc: 'Sell your data to anyone. Access your VM disk contents. Share your information with advertisers. Mine your data for AI training.',
            },
            {
              title: 'Your Rights',
              desc: 'Access, correct, or delete your personal data at any time. Request a full export of everything we hold. No questions asked, no delays.',
            },
            {
              title: 'Security',
              desc: 'AES-256 encryption at rest, TLS 1.2+ in transit. SOC 2 aligned controls, regular third-party security audits, and role-based access throughout.',
            },
          ]}
        />

        <div style={{maxWidth: 800, margin: '0 auto'}}>
          <div className={styles.featureCard} style={{padding: '3rem'}}>
            {(
              [
                {
                  title: '1. Introduction',
                  content: `Zyvor ("we", "us", or "our") is the trade name of ${LEGAL_ENTITY_INDIA.legalName}, a company incorporated in India under the Companies Act, 2013 (CIN ${LEGAL_ENTITY_INDIA.cin}). We are committed to protecting the privacy of our users, customers, and website visitors. This Privacy Policy describes how we collect, use, disclose, and safeguard your information when you visit our website, use the HyperSDK Platform, or interact with our services.`,
                },
                {
                  title: '2. Information We Collect',
                  content:
                    'We collect information that you provide directly to us, including: contact information (name, email address, company name) when you request a demo, create an account, or contact us; usage data when you interact with the HyperSDK Platform, including API calls, migration job metadata, and dashboard activity; and technical data such as browser type, IP address, and device information collected automatically through cookies and similar technologies. For the public marketing website, we may retain IP addresses in an admin-only visit log for up to 90 days to analyze traffic sources and geographic trends.',
                },
                {
                  title: '3. How We Use Your Information',
                  content:
                    'We use the information we collect to: provide, maintain, and improve the HyperSDK Platform and services; process and complete migration operations you initiate; send you technical notices, updates, and support communications; respond to your comments, questions, and customer service requests; monitor and analyze usage trends to improve user experience; and detect, investigate, and prevent fraudulent transactions or unauthorized access.',
                },
                {
                  title: '4. Data Security',
                  content:
                    'We implement industry-standard security measures to protect your data, including: encryption of data in transit using TLS 1.2 or higher; encryption of data at rest using AES-256; role-based access controls (RBAC) for platform access; comprehensive audit logging of all data access and migration operations; regular security assessments and penetration testing; and SOC2-aligned operational procedures.',
                },
                {
                  title: '5. Data Retention',
                  content:
                    "We retain your personal information for as long as your account is active or as needed to provide services. Migration job metadata and audit logs are retained in accordance with your organization's configured retention policies. You may request deletion of your personal data at any time by contacting us.",
                },
                {
                  title: '6. Third-Party Services',
                  content:
                    'The HyperSDK Platform integrates with third-party cloud providers (AWS, Azure, GCP, OCI, and others) to perform VM migration operations. When you configure provider integrations, your credentials and data are transmitted directly to those providers in accordance with their respective privacy policies. We do not store your cloud provider credentials beyond the encrypted session in which they are used.',
                },
                {
                  title: '7. Cookies & Consent',
                  anchor: 'cookie-preferences',
                  content:
                    'Our website uses strictly necessary cookies to operate and, only with your consent, analytics cookies to understand traffic sources and improve the experience. A consent banner is shown on your first visit. You can change or withdraw your choice at any time by selecting "Cookie Preferences" in the site footer, which reopens the consent controls. Strictly necessary cookies cannot be switched off, as the site depends on them to function.',
                },
                {
                  title: '8. Your Rights',
                  content:
                    'Depending on your jurisdiction, you may have the right to: access the personal data we hold about you; request correction of inaccurate data; request deletion of your data; object to or restrict processing of your data; data portability; and withdraw consent where processing is based on consent. To exercise any of these rights, please contact us using the information in the Contact Us section below.',
                },
                {
                  title: '9. Changes to This Policy',
                  content:
                    'We may update this Privacy Policy from time to time. We will notify you of any material changes by posting the new Privacy Policy on this page and updating the "Last Updated" date. Your continued use of the platform after changes constitutes acceptance of the updated policy.',
                },
                {
                  title: '10. Contact Us',
                  content: `If you have any questions about this Privacy Policy or our data practices, please contact us at: ${EMAIL_INFO}.`,
                },
              ] as {title: string; content: string; anchor?: string}[]
            ).map((section, i, arr) => (
              <div
                key={section.title}
                id={section.anchor}
                style={{marginBottom: i < arr.length - 1 ? '2rem' : 0, scrollMarginTop: '90px'}}
              >
                <h2
                  style={{
                    fontSize: '1.3rem',
                    fontWeight: 700,
                    color: 'var(--hs-text-heading)',
                    marginBottom: '0.75rem',
                  }}
                >
                  {section.title}
                </h2>
                <p
                  style={{
                    color: 'var(--hs-text-muted)',
                    fontSize: '0.95rem',
                    lineHeight: 1.8,
                    margin: 0,
                  }}
                >
                  {section.content}
                </p>
              </div>
            ))}
          </div>
        </div>
      </PageContent>
    </ProductPage>
  );
}
