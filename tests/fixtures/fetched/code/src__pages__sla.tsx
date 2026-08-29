// Copyright (c) 2026 ZyvorAI Labs Private Limited. All rights reserved.
// Proprietary software — see LICENSE in the repository root.
// https://zyvor.dev · info@zyvor.dev

import type {ReactNode} from 'react';
import {EMAIL_SALES} from '../data/emails';
import {ProductPage, PageContent, SectionHeader, FeatureGrid, styles, MarketingHero} from '../components/shared';

const uptimeTiers = [
  {
    title: 'Community',
    desc: '99.0% monthly uptime. Ideal for development and non-critical workloads. Community forum support with best-effort response times.',
  },
  {
    title: 'Professional',
    desc: '99.9% monthly uptime. Built for production workloads requiring reliable availability. Email and chat support with guaranteed response windows.',
  },
  {
    title: 'Enterprise',
    desc: '99.95% monthly uptime. Mission-critical tier with dedicated infrastructure, priority routing, and a named Technical Account Manager.',
  },
];

export default function SLA(): ReactNode {
  return (
    <ProductPage
      title="Service Level Agreement"
      description="HyperSDK Platform SLA — uptime commitments, response times, and credit policies for every tier from Zyvor."
    >
      <MarketingHero pageId="sla" />

      <PageContent>
        {/* Uptime Tiers */}
        <SectionHeader
          eyebrow="Uptime"
          title="Availability Commitments"
          subtitle="Each tier defines a minimum Monthly Uptime Percentage. Uptime is measured as total minutes in the calendar month minus downtime minutes, divided by total minutes."
        />
        <FeatureGrid features={uptimeTiers} columns={3} />

        {/* What Uptime Means */}
        <SectionHeader
          eyebrow="Context"
          title="What Uptime Means"
          subtitle="Uptime percentages can be abstract. Here is what each SLA tier translates to in actual allowed downtime."
        />
        <div style={{overflowX: 'auto', margin: '0 auto 3rem', maxWidth: 900}}>
          <table
            className={styles.featureCard}
            style={{
              width: '100%',
              borderCollapse: 'collapse',
              textAlign: 'left',
            }}
          >
            <thead>
              <tr style={{borderBottom: '2px solid var(--ifm-color-emphasis-300)'}}>
                <th style={{padding: '1rem'}}>SLA</th>
                <th style={{padding: '1rem'}}>Monthly Downtime</th>
                <th style={{padding: '1rem'}}>Annual Downtime</th>
              </tr>
            </thead>
            <tbody>
              {[
                {sla: '99.0%', monthly: '7h 18min', annual: '3d 15h 36min'},
                {sla: '99.9%', monthly: '43min 50s', annual: '8h 45min 36s'},
                {sla: '99.95%', monthly: '21min 55s', annual: '4h 22min 48s'},
                {sla: '99.99%', monthly: '4min 23s', annual: '52min 34s'},
              ].map((row, i, arr) => (
                <tr
                  key={row.sla}
                  style={i < arr.length - 1 ? {borderBottom: '1px solid var(--ifm-color-emphasis-200)'} : undefined}
                >
                  <td style={{padding: '1rem'}}>
                    <strong style={{color: 'var(--hs-accent-light)', fontFamily: 'var(--hs-font-mono)'}}>
                      {row.sla}
                    </strong>
                  </td>
                  <td style={{padding: '1rem', color: 'var(--hs-text-body)'}}>{row.monthly}</td>
                  <td style={{padding: '1rem', color: 'var(--hs-text-body)'}}>{row.annual}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Response Time Table */}
        <SectionHeader
          eyebrow="Support"
          title="Response Time Targets"
          subtitle="Initial response times vary by severity level and your subscription tier. All times are measured during business hours (24x7 for Enterprise Critical)."
        />
        <div style={{overflowX: 'auto', margin: '0 auto 3rem', maxWidth: 900}}>
          <table
            className={styles.featureCard}
            style={{
              width: '100%',
              borderCollapse: 'collapse',
              textAlign: 'left',
            }}
          >
            <thead>
              <tr style={{borderBottom: '2px solid var(--ifm-color-emphasis-300)'}}>
                <th style={{padding: '1rem'}}>Severity</th>
                <th style={{padding: '1rem'}}>Community</th>
                <th style={{padding: '1rem'}}>Professional</th>
                <th style={{padding: '1rem'}}>Enterprise</th>
              </tr>
            </thead>
            <tbody>
              <tr style={{borderBottom: '1px solid var(--ifm-color-emphasis-200)'}}>
                <td style={{padding: '1rem'}}>
                  <strong>Critical</strong> — Platform down, no workaround
                </td>
                <td style={{padding: '1rem'}}>4 hours</td>
                <td style={{padding: '1rem'}}>2 hours</td>
                <td style={{padding: '1rem'}}>1 hour</td>
              </tr>
              <tr style={{borderBottom: '1px solid var(--ifm-color-emphasis-200)'}}>
                <td style={{padding: '1rem'}}>
                  <strong>High</strong> — Major feature impaired
                </td>
                <td style={{padding: '1rem'}}>24 hours</td>
                <td style={{padding: '1rem'}}>8 hours</td>
                <td style={{padding: '1rem'}}>4 hours</td>
              </tr>
              <tr style={{borderBottom: '1px solid var(--ifm-color-emphasis-200)'}}>
                <td style={{padding: '1rem'}}>
                  <strong>Medium</strong> — Minor feature issue, workaround exists
                </td>
                <td style={{padding: '1rem'}}>48 hours</td>
                <td style={{padding: '1rem'}}>24 hours</td>
                <td style={{padding: '1rem'}}>8 hours</td>
              </tr>
              <tr>
                <td style={{padding: '1rem'}}>
                  <strong>Low</strong> — General question or feature request
                </td>
                <td style={{padding: '1rem'}}>Best effort</td>
                <td style={{padding: '1rem'}}>48 hours</td>
                <td style={{padding: '1rem'}}>24 hours</td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Credit Policy */}
        <SectionHeader
          eyebrow="Credits"
          title="Downtime Credit Policy"
          subtitle="If Zyvor fails to meet the uptime commitment for the HyperSDK Platform for your tier, you may request service credits applied to future invoices."
        />
        <div style={{overflowX: 'auto', margin: '0 auto 3rem', maxWidth: 900}}>
          <table
            className={styles.featureCard}
            style={{
              width: '100%',
              borderCollapse: 'collapse',
              textAlign: 'left',
            }}
          >
            <thead>
              <tr style={{borderBottom: '2px solid var(--ifm-color-emphasis-300)'}}>
                <th style={{padding: '1rem'}}>Monthly Uptime</th>
                <th style={{padding: '1rem'}}>Credit (% of Monthly Fee)</th>
              </tr>
            </thead>
            <tbody>
              <tr style={{borderBottom: '1px solid var(--ifm-color-emphasis-200)'}}>
                <td style={{padding: '1rem'}}>Below SLA but above 99.0%</td>
                <td style={{padding: '1rem'}}>10%</td>
              </tr>
              <tr style={{borderBottom: '1px solid var(--ifm-color-emphasis-200)'}}>
                <td style={{padding: '1rem'}}>98.0% to 99.0%</td>
                <td style={{padding: '1rem'}}>25%</td>
              </tr>
              <tr>
                <td style={{padding: '1rem'}}>Below 98.0%</td>
                <td style={{padding: '1rem'}}>50%</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div className={styles.featureCard} style={{textAlign: 'left', maxWidth: 900, margin: '0 auto 3rem'}}>
          <h3>Credit Request Process</h3>
          <ol>
            <li>
              Submit a credit request via the <a href="/contact">support portal</a> within 30 days of the affected
              month.
            </li>
            <li>Include the dates and times of observed downtime.</li>
            <li>Zyvor will validate the claim against internal monitoring data within 5 business days.</li>
            <li>Approved credits are applied to your next invoice and do not expire for 12 months.</li>
          </ol>
          <h3>Exclusions</h3>
          <p>The following are excluded from uptime calculations:</p>
          <ul>
            <li>Scheduled maintenance communicated at least 72 hours in advance.</li>
            <li>
              Downtime caused by factors outside Zyvor&apos; control (force majeure, network provider outages,
              DNS issues).
            </li>
            <li>Issues resulting from customer misconfigurations or unauthorized modifications.</li>
            <li>Alpha or beta features explicitly marked as not covered by SLA.</li>
          </ul>
        </div>

        <div className={styles.featureCard} style={{textAlign: 'left', maxWidth: 900, margin: '0 auto'}}>
          <h3>Questions?</h3>
          <p>
            For questions about this SLA or to discuss Enterprise-tier terms, contact us at{' '}
            <a href={`mailto:${EMAIL_SALES}`}>{EMAIL_SALES}</a> or visit our <a href="/contact">Contact page</a>.
          </p>
        </div>
      </PageContent>
    </ProductPage>
  );
}
