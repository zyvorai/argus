// Copyright (c) 2026 ZyvorAI Labs Private Limited. All rights reserved.
// Proprietary software — see LICENSE in the repository root.
// https://zyvor.dev · info@zyvor.dev

import {useEffect, useMemo, useRef, useState} from 'react';
import type {ReactNode} from 'react';
import {useLocation} from '@docusaurus/router';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import FAQAccordion from '../components/FAQAccordion';
import {ProductPage, MarketingHero, PageContent, styles} from '../components/shared';
import {getHomeHeroCopy} from '../data/homepage-locale';
import {getContactFormCopy, getContactIntentLocaleCopy, getContactTrialExtras} from '../data/contact-locale';
import {formatRoiPrefillMessage, parseRoiPrefillFromSearch} from '../utils/roiContactPrefill';
import {formatAssessmentPrefillMessage, parseAssessmentPrefillFromSearch} from '../utils/assessmentContactPrefill';
import {formatPresentationPrefillMessage, parsePresentationPathFromSearch} from '../utils/presentationContactPrefill';
import type {MarketingPageHeroId} from '../data/marketing-page-heroes';
import {EMAIL_INFO, EMAIL_SALES} from '../data/emails';
import {LEGAL_ENTITY_INDIA} from '../data/legal-entity-india';
import {useFormspree} from '../hooks/useFormspree';
import {getMarketingAttribution, getPulseTrackingFields} from '../utils/marketingAttribution';
import {dispatchMarketingEvent} from '../utils/marketingEvents';

const roles = [
  'Engineering Manager',
  'DevOps / SRE',
  'Infrastructure Engineer',
  'VP / Director of Engineering',
  'CTO / CIO',
  'Solutions Architect',
  'Other',
];

type ContactIntentConfig = {
  heroPageId: MarketingPageHeroId;
  asideTitle: string;
  asideBullets: string[];
  submitLabel: string;
  messagePlaceholder: string;
};

const intentConfig: Record<string, ContactIntentConfig> = {
  trial: {
    heroPageId: 'contact-demo',
    asideTitle: '14-day Starter trial',
    asideBullets: [
      'Full Starter tier access — no credit card required',
      'Solutions engineering onboarding within one business day',
      'Dashboard access available after environment review',
    ],
    submitLabel: 'Request free trial',
    messagePlaceholder: 'VM count, hypervisor mix, and preferred start date…',
  },
  sales: {
    heroPageId: 'contact',
    asideTitle: 'Talk to sales',
    asideBullets: [
      'Licensing, enterprise programs, and multi-site rollouts',
      'ROI and TCO models for your VM estate',
      'Procurement-friendly quotes and deployment planning',
    ],
    submitLabel: 'Contact sales',
    messagePlaceholder: 'Company, VM count, timeline, and how we can help…',
  },
  demo: {
    heroPageId: 'contact-demo',
    asideTitle: 'What to expect in your demo',
    asideBullets: [
      'Live walkthrough of export, conversion, and dashboard workflows',
      'Tailored to your hypervisor mix (VMware, cloud, OpenStack)',
      'Q&A with solutions engineering — typically 30 minutes',
    ],
    submitLabel: 'Request demo',
    messagePlaceholder: 'Hypervisor mix, VM count, target platform, and timeline…',
  },
  'savings-report': {
    heroPageId: 'contact-savings',
    asideTitle: 'Your custom savings report',
    asideBullets: [
      'VMware licensing vs HyperSDK Platform TCO model for your VM count',
      'Public-cloud run-rate comparison for steady-state workloads',
      'Typical payback window from recent customer programs',
    ],
    submitLabel: 'Get savings estimate',
    messagePlaceholder: 'Approximate VM count, current VMware/cloud spend, and goals…',
  },
  assessment: {
    heroPageId: 'contact-assessment',
    asideTitle: 'Migration assessment scope',
    asideBullets: [
      'Inventory and dependency mapping for wave planning',
      'Risk, rollback, and cutover sequencing recommendations',
      'VMware exit, repatriation, or KubeVirt fleet options',
    ],
    submitLabel: 'Book assessment',
    messagePlaceholder: 'Source platforms, VM count, compliance constraints, and target date…',
  },
  'vmware-exit': {
    heroPageId: 'contact-vmware-exit',
    asideTitle: 'VMware exit program',
    asideBullets: [
      'Licensing TCO model vs KVM / KubeVirt targets',
      'Wave plan with rollback-safe export and conversion',
      'VirtIO, bootloader, and first-boot validation on your estate',
    ],
    submitLabel: 'Request VMware exit assessment',
    messagePlaceholder: 'vSphere version, VM count, target platform, and renewal timeline…',
  },
  windows: {
    heroPageId: 'contact-assessment',
    asideTitle: 'Windows migration program',
    asideBullets: [
      'Driver injection and boot repair for AD-joined workloads',
      'Pre-migration disk scans with GuestKit',
      'Pilot wave before production cutover',
    ],
    submitLabel: 'Request Windows assessment',
    messagePlaceholder: 'Windows versions, VM count, domain join requirements…',
  },
  linux: {
    heroPageId: 'contact-assessment',
    asideTitle: 'Linux fleet migration',
    asideBullets: [
      'Batch exports across RHEL, Ubuntu, SUSE, and Debian',
      'API-first and GitOps-friendly migration factories',
      'Multi-hypervisor sources into standardized KVM images',
    ],
    submitLabel: 'Talk to engineering',
    messagePlaceholder: 'Distro mix, VM count, source hypervisors, and timeline…',
  },
  repatriation: {
    heroPageId: 'contact-savings',
    asideTitle: 'Cloud repatriation workshop',
    asideBullets: [
      'Egress-aware migration waves from AWS, Azure, GCP, or OCI',
      'Steady-state TCO vs public-cloud run-rate modeling',
      'Hybrid rollback paths during repatriation',
    ],
    submitLabel: 'Request repatriation workshop',
    messagePlaceholder: 'Cloud provider(s), workload types, monthly spend, target platform…',
  },
  airgap: {
    heroPageId: 'contact-assessment',
    asideTitle: 'Air-gapped deployment',
    asideBullets: [
      'Offline export bundles and sneakernet-friendly workflows',
      'Regulated-environment sequencing and audit trails',
      'hyper2kvm and GuestKit without outbound connectivity',
    ],
    submitLabel: 'Request air-gap briefing',
    messagePlaceholder: 'Compliance regime, site count, connectivity constraints…',
  },
  edge: {
    heroPageId: 'contact-demo',
    asideTitle: 'Edge deployment',
    asideBullets: [
      'Retail, factory, and remote-site migration patterns',
      'Offline export with central control plane options',
      'Low-touch operations for distributed estates',
    ],
    submitLabel: 'Discuss edge deployment',
    messagePlaceholder: 'Site count, connectivity, VM footprint, and targets…',
  },
  database: {
    heroPageId: 'contact-assessment',
    asideTitle: 'Database-tier VM migration',
    asideBullets: [
      'Integrity checks and index validation before cutover',
      'Database-tier guest fixes and replication-aware waves',
      'Post-migration health baselines',
    ],
    submitLabel: 'Plan database migration',
    messagePlaceholder: 'Database engines, VM count, RPO/RTO requirements…',
  },
  partners: {
    heroPageId: 'contact',
    asideTitle: 'Partnership programs',
    asideBullets: [
      'Technology and services partner onboarding',
      'Co-sell and implementation support',
      'Certified integration paths',
    ],
    submitLabel: 'Contact partnerships',
    messagePlaceholder: 'Partner type, regions, and integration focus…',
  },
  compliance: {
    heroPageId: 'contact-assessment',
    asideTitle: 'Security & compliance briefing',
    asideBullets: [
      'RBAC, audit logging, and encryption overview',
      'Mappings to SOC 2, HIPAA, and FedRAMP-style controls',
      'Regulated migration sequencing',
    ],
    submitLabel: 'Schedule security review',
    messagePlaceholder: 'Frameworks in scope, audit timeline, deployment model…',
  },
  support: {
    heroPageId: 'contact',
    asideTitle: 'Platform support',
    asideBullets: [
      'Production incident and escalation paths',
      'Dashboard, API, and migration workflow issues',
      'Enterprise SLA programs',
    ],
    submitLabel: 'Contact support',
    messagePlaceholder: 'Environment, product area, and issue summary…',
  },
};

const defaultIntentConfig: ContactIntentConfig = {
  heroPageId: 'contact',
  asideTitle: 'Enterprise-ready from day one',
  asideBullets: [
    'VMware exit, cloud repatriation, and KubeVirt fleet programs',
    'Air-gapped and regulated deployment options',
    'Solutions engineering within one business day',
  ],
  submitLabel: 'Send message',
  messagePlaceholder: 'Tell us about your migration requirements…',
};

export default function Contact(): ReactNode {
  const {i18n, siteConfig} = useDocusaurusContext();
  const homeCopy = getHomeHeroCopy(i18n.currentLocale);
  const dashboardUrl = (siteConfig.customFields?.dashboardUrl as string) || 'https://dashboard.zyvor.dev';
  const {status, submit, error, mailHint} = useFormspree();
  const {search} = useLocation();
  const intent = useMemo(() => {
    const value = new URLSearchParams(search).get('intent');
    return value || 'general';
  }, [search]);
  const baseConfig = intentConfig[intent] ?? defaultIntentConfig;
  const localeCopy = getContactIntentLocaleCopy(intent, i18n.currentLocale);
  const config = localeCopy ? {...baseConfig, ...localeCopy} : baseConfig;
  const formCopy = getContactFormCopy(i18n.currentLocale);
  const attribution = useMemo(() => ({...getMarketingAttribution(), ...getPulseTrackingFields()}), [search]);
  const roiPrefill = useMemo(() => parseRoiPrefillFromSearch(search), [search]);
  const assessmentPrefill = useMemo(() => parseAssessmentPrefillFromSearch(search), [search]);
  const presentationPath = useMemo(() => parsePresentationPathFromSearch(search), [search]);
  const presentationPrefill = useMemo(
    () => (presentationPath ? formatPresentationPrefillMessage(presentationPath) : ''),
    [presentationPath],
  );
  const prefillMessage = useMemo(() => formatRoiPrefillMessage(roiPrefill), [roiPrefill]);
  const assessmentMessage = useMemo(() => formatAssessmentPrefillMessage(assessmentPrefill), [assessmentPrefill]);
  const nameInputRef = useRef<HTMLInputElement>(null);
  const formStartedRef = useRef(false);
  const [vmCountDefault, setVmCountDefault] = useState('');
  const [messageDefault, setMessageDefault] = useState('');

  useEffect(() => {
    if (roiPrefill.vmCount) {
      setVmCountDefault(String(roiPrefill.vmCount));
    }
    if (intent === 'savings-report' && prefillMessage) {
      setMessageDefault(prefillMessage);
    } else if (intent === 'assessment' && assessmentPrefill.answers.length > 0) {
      setMessageDefault(assessmentMessage);
    } else if (presentationPrefill) {
      setMessageDefault(presentationPrefill);
    }
  }, [
    roiPrefill.vmCount,
    intent,
    prefillMessage,
    assessmentPrefill.answers.length,
    assessmentMessage,
    presentationPrefill,
  ]);

  useEffect(() => {
    if (status === 'idle' && nameInputRef.current) {
      nameInputRef.current.focus();
    }
  }, [status, intent]);

  useEffect(() => {
    if (status === 'error') {
      dispatchMarketingEvent('contact_form_error', {intent});
    }
  }, [status, intent]);

  return (
    <ProductPage
      title="Contact Us"
      description="Reach Zyvor — schedule a demo, pricing, or talk to a HyperSDK Platform expert."
    >
      <MarketingHero pageId={config.heroPageId} />

      <PageContent>
        <div className={styles.contactLayout}>
          <aside className={styles.contactAside}>
            <div className={styles.featureCard} style={{textAlign: 'left', padding: '2rem'}}>
              <span className={styles.sectionEyebrow}>Why teams reach out</span>
              <h2 style={{color: 'var(--hs-text-heading)', fontSize: '1.35rem', fontWeight: 700, margin: '0 0 1rem'}}>
                {config.asideTitle}
              </h2>
              <ul className={styles.contactTrustList}>
                {config.asideBullets.map((bullet) => (
                  <li key={bullet}>
                    <span className={styles.contactTrustIcon} aria-hidden>
                      ✓
                    </span>
                    {bullet}
                  </li>
                ))}
              </ul>
              <p style={{color: 'var(--hs-text-muted)', fontSize: '0.9rem', marginTop: '1.5rem', marginBottom: 0}}>
                Or email{' '}
                <a href={`mailto:${EMAIL_SALES}`} style={{color: 'var(--hs-accent-light)'}}>
                  {EMAIL_SALES}
                </a>
              </p>
              {intent === 'trial' ? (
                <p style={{marginTop: '1.25rem', marginBottom: 0}}>
                  <span
                    style={{
                      display: 'block',
                      color: 'var(--hs-text-muted)',
                      fontSize: '0.88rem',
                      marginBottom: '0.65rem',
                    }}
                  >
                    {getContactTrialExtras(i18n.currentLocale).dashboardPrompt}
                  </span>
                  <a
                    href={dashboardUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={styles.primaryBtn}
                    style={{display: 'inline-flex', fontSize: '0.9rem', padding: '0.55rem 1rem'}}
                  >
                    {getContactTrialExtras(i18n.currentLocale).openDashboard}
                  </a>
                </p>
              ) : null}
            </div>

            <div
              className={styles.featureCard}
              style={{textAlign: 'left', padding: '1.5rem', marginTop: '1.25rem', fontSize: '0.88rem', lineHeight: 1.8}}
            >
              <span
                style={{
                  display: 'block',
                  fontFamily: 'var(--hs-font-mono)',
                  fontSize: '0.7rem',
                  textTransform: 'uppercase',
                  letterSpacing: '0.1em',
                  color: 'var(--hs-text-muted)',
                  marginBottom: '0.75rem',
                }}
              >
                Registered office
              </span>
              <address style={{fontStyle: 'normal', color: 'var(--hs-text-muted)'}}>
                <strong style={{color: 'var(--hs-text-heading)', display: 'block', marginBottom: '0.25rem'}}>
                  {LEGAL_ENTITY_INDIA.legalName}
                </strong>
                {LEGAL_ENTITY_INDIA.addressOneLine}
                <br />
                CIN:{' '}
                <span style={{fontFamily: 'var(--hs-font-mono)', fontSize: '0.8rem'}}>{LEGAL_ENTITY_INDIA.cin}</span>
              </address>
            </div>
          </aside>
          <div>
            {status === 'done' || status === 'done_no_mail' ? (
              <div
                className={styles.featureCard}
                role="status"
                aria-live="polite"
                style={{
                  border:
                    status === 'done_no_mail'
                      ? '1px solid rgba(245, 158, 11, 0.35)'
                      : '1px solid rgba(34, 197, 94, 0.3)',
                  textAlign: 'center',
                  padding: '3rem',
                }}
              >
                <h2
                  style={{
                    color: status === 'done_no_mail' ? 'var(--hs-warning, #f59e0b)' : 'var(--hs-success)',
                    fontSize: '1.5rem',
                    fontWeight: 700,
                    marginBottom: '0.75rem',
                  }}
                >
                  {status === 'done_no_mail' ? "We've saved your message" : 'Thank you!'}
                </h2>
                <p style={{color: 'var(--hs-text-muted)', fontSize: '1rem'}}>
                  {status === 'done_no_mail' ? (
                    <>
                      Your details were received, but we could not send the notification email from our server. Please
                      email{' '}
                      <a href={`mailto:${EMAIL_INFO}`} style={{color: 'var(--hs-text-heading)'}}>
                        {EMAIL_INFO}
                      </a>{' '}
                      so we can follow up.
                      {mailHint ? (
                        <span style={{display: 'block', marginTop: '0.75rem', fontSize: '0.9rem', opacity: 0.95}}>
                          {mailHint}
                        </span>
                      ) : null}
                    </>
                  ) : (
                    "We've received your message. Our team will be in touch within one business day."
                  )}
                </p>
              </div>
            ) : (
              <div className={styles.featureCard}>
                <form
                  aria-busy={status === 'sending'}
                  onSubmit={async (e) => {
                    e.preventDefault();
                    const ok = await submit(new FormData(e.currentTarget));
                    if (ok) {
                      dispatchMarketingEvent('contact_form_submit', {intent});
                    }
                  }}
                >
                  <span className="sr-only" role="status" aria-live="polite">
                    {status === 'sending' ? formCopy.sending : ''}
                  </span>
                  <input type="hidden" name="_intent" value={intent} />
                  {Object.entries(attribution).map(([key, value]) => (
                    <input key={key} type="hidden" name={key} value={value} />
                  ))}
                  <div className="hp-field" aria-hidden="true">
                    <label htmlFor="contact-hp">Leave blank</label>
                    <input id="contact-hp" name="_gotcha" type="text" tabIndex={-1} autoComplete="off" />
                  </div>
                  <div className={styles.formGrid2}>
                    <div>
                      <label htmlFor="contact-name" className={styles.formLabel}>
                        {formCopy.name}
                      </label>
                      <input
                        ref={nameInputRef}
                        id="contact-name"
                        name="name"
                        type="text"
                        required
                        autoComplete="name"
                        className={styles.formInput}
                        placeholder="Jane Smith"
                        aria-invalid={status === 'error' ? true : undefined}
                        onFocus={() => {
                          if (!formStartedRef.current) {
                            formStartedRef.current = true;
                            dispatchMarketingEvent('contact_form_started', {intent});
                          }
                        }}
                      />
                    </div>
                    <div>
                      <label htmlFor="contact-email" className={styles.formLabel}>
                        {formCopy.email}
                      </label>
                      <input
                        id="contact-email"
                        name="email"
                        type="email"
                        required
                        autoComplete="email"
                        className={styles.formInput}
                        placeholder="jane@company.com"
                      />
                    </div>
                  </div>

                  <div className={styles.formGrid2}>
                    <div>
                      <label htmlFor="contact-company" className={styles.formLabel}>
                        {formCopy.company}
                      </label>
                      <input
                        id="contact-company"
                        name="company"
                        type="text"
                        required
                        autoComplete="organization"
                        className={styles.formInput}
                        placeholder="Acme Corp"
                      />
                    </div>
                    <div>
                      <label htmlFor="contact-role" className={styles.formLabel}>
                        {formCopy.role}
                      </label>
                      <select id="contact-role" name="role" className={styles.formInput}>
                        <option value="">{formCopy.rolePlaceholder}</option>
                        {roles.map((r) => (
                          <option key={r} value={r}>
                            {r}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div className={styles.formGroup}>
                    <label htmlFor="contact-vm-count" className={styles.formLabel}>
                      {formCopy.vmCount}
                    </label>
                    <input
                      id="contact-vm-count"
                      name="vm_count"
                      type="number"
                      min="1"
                      max="100000"
                      className={styles.formInput}
                      placeholder={formCopy.vmPlaceholder}
                      defaultValue={vmCountDefault}
                      key={`vm-${vmCountDefault}`}
                    />
                  </div>

                  <div className={styles.formGroup}>
                    <label htmlFor="contact-message" className={styles.formLabel}>
                      {formCopy.message}
                    </label>
                    <textarea
                      id="contact-message"
                      name="message"
                      rows={4}
                      className={styles.formInput}
                      style={{resize: 'vertical'}}
                      placeholder={config.messagePlaceholder}
                      defaultValue={messageDefault}
                      key={`msg-${messageDefault.slice(0, 24)}`}
                    />
                  </div>

                  {status === 'error' && (
                    <div id="contact-form-error" className={styles.formError} role="alert">
                      {error || 'Something went wrong. Please try again or email us directly.'}
                    </div>
                  )}

                  <button
                    type="submit"
                    disabled={status === 'sending'}
                    aria-describedby={status === 'error' ? 'contact-form-error' : undefined}
                    className={status === 'sending' ? styles.formSubmitBtnDisabled : styles.formSubmitBtn}
                  >
                    {status === 'sending' ? 'Sending…' : config.submitLabel}
                  </button>
                </form>

                <div
                  style={{
                    marginTop: '2rem',
                    paddingTop: '1.5rem',
                    borderTop: '1px solid var(--hs-border)',
                    textAlign: 'center',
                  }}
                >
                  <p style={{color: 'var(--hs-text-subtle)', fontSize: '0.9rem', marginBottom: '0.5rem'}}>
                    Or reach us directly (Zoho Mail)
                  </p>
                  <p style={{color: 'var(--hs-text-muted)', fontSize: '0.95rem', marginBottom: '0.35rem'}}>
                    General:{' '}
                    <a href={`mailto:${EMAIL_INFO}`} style={{color: 'inherit', textDecoration: 'none'}}>
                      {EMAIL_INFO}
                    </a>
                  </p>
                  <p style={{color: 'var(--hs-text-muted)', fontSize: '0.95rem', margin: 0}}>
                    Sales & demos:{' '}
                    <a href={`mailto:${EMAIL_SALES}`} style={{color: 'inherit', textDecoration: 'none'}}>
                      {EMAIL_SALES}
                    </a>
                  </p>
                </div>
              </div>
            )}

            <div className={styles.featureCard} style={{textAlign: 'center', marginTop: '2rem'}}>
              <h3
                style={{color: 'var(--hs-text-heading)', fontSize: '1.2rem', fontWeight: 700, marginBottom: '0.5rem'}}
              >
                Prefer a live walkthrough?
              </h3>
              <p style={{color: 'var(--hs-text-muted)', fontSize: '0.9rem', marginBottom: '1rem'}}>
                Book a 30-minute demo with our solutions engineering team.
              </p>
              <a href="/demo" className={styles.secondaryBtn} style={{display: 'inline-flex'}}>
                Watch Live Demo
              </a>
            </div>

            <div style={{marginTop: '3.5rem'}}>
              <h2
                style={{
                  color: 'var(--hs-text-heading)',
                  fontSize: '1.5rem',
                  fontWeight: 700,
                  marginBottom: '0.5rem',
                  textAlign: 'center',
                }}
              >
                {homeCopy.sectionFaqTitle}
              </h2>
              <p
                style={{
                  color: 'var(--hs-text-muted)',
                  fontSize: '0.95rem',
                  textAlign: 'center',
                  marginBottom: '1.5rem',
                }}
              >
                {homeCopy.sectionFaqSubtitle}
              </p>
              <FAQAccordion limit={4} showViewAll />
            </div>
          </div>
        </div>
      </PageContent>
    </ProductPage>
  );
}
