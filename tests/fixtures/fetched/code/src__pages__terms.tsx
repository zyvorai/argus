// Copyright (c) 2026 ZyvorAI Labs Private Limited. All rights reserved.
// Proprietary software — see LICENSE in the repository root.
// https://zyvor.dev · info@zyvor.dev

import type {ReactNode} from 'react';
import {EMAIL_INFO} from '../data/emails';
import {LEGAL_ENTITY_INDIA} from '../data/legal-entity-india';
import {ProductPage, PageContent, styles, MarketingHero} from '../components/shared';

export default function Terms(): ReactNode {
  return (
    <ProductPage
      title="Terms of Service"
      description="Terms of Service for the HyperSDK Platform — the legal agreement governing use of our platform and services from Zyvor."
    >
      <MarketingHero pageId="terms" />

      <PageContent>
        {/* Key Points */}
        <div
          className={styles.featureCard}
          style={{
            textAlign: 'left',
            maxWidth: 900,
            margin: '0 auto 2rem',
            padding: '2.5rem',
            border: '1px solid rgba(240, 88, 58, 0.2)',
            background: 'rgba(240, 88, 58, 0.03)',
          }}
        >
          <h2
            style={{
              fontSize: '1.3rem',
              fontWeight: 700,
              color: 'var(--hs-text-heading)',
              marginBottom: '1.25rem',
            }}
          >
            Key Points
          </h2>
          <ul
            style={{
              listStyle: 'none',
              padding: 0,
              margin: 0,
              display: 'flex',
              flexDirection: 'column',
              gap: '0.85rem',
            }}
          >
            {[
              {
                bold: 'You own your data',
                rest: ' -- we never claim rights to your VMs, configurations, or any content you process through the HyperSDK Platform.',
              },
              {
                bold: 'Standard SaaS terms',
                rest: ' -- subscription-based pricing, cancel anytime with 30 days notice. No long-term lock-in.',
              },
              {
                bold: 'Fair use',
                rest: ' -- the platform is for your internal business use. Reselling or redistribution requires a partner agreement.',
              },
              {
                bold: 'Liability capped',
                rest: ' -- our total liability is limited to 100% of fees you paid in the last 12 months.',
              },
              {
                bold: 'Governing law',
                rest: ' -- these terms are governed by the laws of the State of Delaware, United States.',
              },
            ].map((item) => (
              <li
                key={item.bold}
                style={{
                  color: 'var(--hs-text-muted)',
                  fontSize: '0.92rem',
                  lineHeight: 1.7,
                  paddingLeft: '1.5rem',
                  position: 'relative',
                }}
              >
                <span
                  style={{
                    position: 'absolute',
                    left: 0,
                    color: 'var(--hs-accent-light)',
                    fontWeight: 700,
                  }}
                >
                  {'\u2713'}
                </span>
                <strong style={{color: 'var(--hs-text-heading)'}}>{item.bold}</strong>
                {item.rest}
              </li>
            ))}
          </ul>
        </div>

        <div className={styles.featureCard} style={{textAlign: 'left', maxWidth: 900, margin: '0 auto'}}>
          <p style={{color: 'var(--ifm-color-emphasis-600)', marginBottom: '2rem'}}>
            <strong>Last Updated:</strong> April 10, 2026
          </p>

          <h2>Contracting entity</h2>
          <p>
            The Services are offered by <strong>{LEGAL_ENTITY_INDIA.legalName}</strong> (trade name{' '}
            <strong>{LEGAL_ENTITY_INDIA.tradeName}</strong>), an Indian company registered with the Ministry of
            Corporate Affairs (CIN {LEGAL_ENTITY_INDIA.cin}). Particulars may be verified on{' '}
            <a href={LEGAL_ENTITY_INDIA.mcaVerifyUrl} target="_blank" rel="noopener noreferrer">
              mca.gov.in
            </a>
            . Registered office: {LEGAL_ENTITY_INDIA.addressOneLine}.
          </p>

          <h2>1. Acceptance of Terms</h2>
          <p>
            By accessing or using the HyperSDK Platform, APIs, documentation, dashboards, or any related services
            (collectively, the &quot;Services&quot;), you agree to be bound by these Terms of Service
            (&quot;Terms&quot;). If you are using the Services on behalf of an organization, you represent that you have
            the authority to bind that organization to these Terms. If you do not agree, you must not use the Services.
          </p>

          <h2>2. License Grant</h2>
          <p>
            Subject to your compliance with these Terms and payment of applicable fees, Zyvor grants you a
            limited, non-exclusive, non-transferable, revocable license to access and use the Services solely for your
            internal business operations. You may not sublicense, resell, or distribute the Services or any component
            thereof without prior written consent from Zyvor.
          </p>
          <p>
            Self-hosted software, containers, and customer bundles are governed by the{' '}
            <a href="/license">Proprietary Software License Agreement (deploy EULA)</a>, not open-source terms.
          </p>
          <p>
            All intellectual property rights in and to the Services, including but not limited to software, APIs,
            documentation, dashboards, and trademarks, remain the exclusive property of Zyvor.
          </p>

          <h2>3. Acceptable Use</h2>
          <p>You agree not to:</p>
          <ul>
            <li>Use the Services for any unlawful purpose or in violation of any applicable law or regulation.</li>
            <li>Attempt to gain unauthorized access to any part of the Services, other accounts, or systems.</li>
            <li>
              Reverse engineer, decompile, disassemble, or otherwise attempt to derive the source code of the Services.
            </li>
            <li>Interfere with or disrupt the integrity or performance of the Services or related infrastructure.</li>
            <li>Use the Services to transmit malware, viruses, or any harmful code.</li>
            <li>Exceed documented API rate limits or use automated tools to scrape or overload the platform.</li>
          </ul>

          <h2>4. Data and Privacy</h2>
          <p>
            You retain ownership of all data you upload or process through the Services (&quot;Customer Data&quot;).
            Zyvor will not access, use, or disclose Customer Data except as necessary to provide the Services,
            comply with applicable law, or as otherwise permitted by your agreement with us.
          </p>
          <p>
            Zyvor implements industry-standard security measures to protect Customer Data, including encryption
            at rest and in transit, role-based access controls, and regular security audits. For full details, please
            refer to our <a href="/privacy">Privacy Policy</a> and <a href="/docs/security">Security Documentation</a>.
          </p>

          <h2>5. Service Availability and Support</h2>
          <p>
            Zyvor strives to maintain high availability of the Services. Specific uptime commitments and support
            response times are governed by your <a href="/sla">Service Level Agreement (SLA)</a> tier. Scheduled
            maintenance windows will be communicated in advance and are excluded from uptime calculations.
          </p>

          <h2>6. Fees and Payment</h2>
          <p>
            Fees for the Services are set forth in your order form or subscription agreement. All fees are
            non-refundable except as expressly stated in these Terms or your SLA. Zyvor reserves the right to
            modify pricing with 30 days&apos; prior written notice. Overdue invoices may incur a late fee of 1.5% per
            month or the maximum rate permitted by law, whichever is lower.
          </p>

          <h2>7. Limitation of Liability</h2>
          <p>
            TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, ZYVOR SHALL NOT BE LIABLE FOR ANY INDIRECT,
            INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, OR ANY LOSS OF PROFITS, REVENUE, DATA, OR BUSINESS
            OPPORTUNITY ARISING OUT OF OR RELATED TO THESE TERMS OR THE SERVICES, REGARDLESS OF THE THEORY OF LIABILITY.
          </p>
          <p>
            ZYVOR&apos;S TOTAL AGGREGATE LIABILITY UNDER THESE TERMS SHALL NOT EXCEED ONE HUNDRED PERCENT (100%)
            OF THE FEES PAID BY YOU TO ZYVOR IN THE TWELVE (12) MONTHS PRECEDING THE EVENT GIVING RISE TO THE
            CLAIM.
          </p>

          <h2>8. Indemnification</h2>
          <p>
            You agree to indemnify, defend, and hold harmless Zyvor and its officers, directors, employees, and
            agents from any claims, damages, losses, or expenses (including reasonable attorneys&apos; fees) arising
            from your use of the Services, your violation of these Terms, or your infringement of any third-party
            rights.
          </p>

          <h2>9. Termination</h2>
          <p>
            Either party may terminate these Terms with 30 days&apos; written notice. Zyvor may suspend or
            terminate your access immediately if you breach these Terms or if required by law. Upon termination, your
            license to use the Services ceases immediately. You may request export of your Customer Data within 30 days
            of termination, after which Zyvor may delete it.
          </p>

          <h2>10. Governing Law and Dispute Resolution</h2>
          <p>
            These Terms are governed by the laws of the State of Delaware, United States, without regard to conflict of
            law principles. Any disputes arising under these Terms shall be resolved through binding arbitration
            administered by the American Arbitration Association in accordance with its Commercial Arbitration Rules.
          </p>

          <h2>11. Changes to These Terms</h2>
          <p>
            Zyvor reserves the right to update these Terms at any time. Material changes will be communicated
            via email or a prominent notice on the platform at least 30 days prior to taking effect. Continued use of
            the Services after such changes constitutes acceptance of the revised Terms.
          </p>

          <h2>12. Contact</h2>
          <p>
            If you have questions about these Terms, please contact us at{' '}
            <a href={`mailto:${EMAIL_INFO}`}>{EMAIL_INFO}</a> or visit our <a href="/contact">Contact page</a>.
          </p>
        </div>
      </PageContent>
    </ProductPage>
  );
}
