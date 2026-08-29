// Copyright (c) 2026 ZyvorAI Labs Private Limited. All rights reserved.
// Proprietary software — see LICENSE in the repository root.
// https://zyvor.dev · info@zyvor.dev

import {useState, type FormEvent, type ReactNode} from 'react';
import Link from '@docusaurus/Link';
import {
  ProductPage,
  PageContent,
  SectionHeader,
  FeatureGrid,
  styles,
  MarketingHero,
  CTASection,
} from '../components/shared';
import {platform} from '../data/platform-stats';
import {useFormspree} from '../hooks/useFormspree';
import {captureMarketingAttribution, getMarketingAttribution} from '../utils/marketingAttribution';
import {dispatchMarketingEvent} from '../utils/marketingEvents';
import {EMAIL_INFO} from '../data/emails';

const insidePoints = [
  'Cost analysis: VMware vs KVM total cost of ownership over 3 years',
  'Migration timeline: Step-by-step 90-day migration plan used by Fortune 500 teams',
  `Risk mitigation: How to achieve ${platform.firstBootSuccess} first-boot success rate with zero downtime`,
  'Case studies: 3 enterprises that saved $720K-$1.2M annually after migrating',
];

const chapters = [
  {
    number: '01',
    title: 'The True Cost of VMware',
    desc: 'Licensing escalation, support costs, and vendor lock-in quantified. Broadcom acquisition impact analysis with real numbers from enterprise customers.',
    accent: '#ef4444',
  },
  {
    number: '02',
    title: 'Migration Timeline & Planning',
    desc: 'The proven 30/60/90 day approach: discovery and assessment in month one, pilot migrations in month two, full production cutover in month three.',
    accent: '#3b82f6',
  },
  {
    number: '03',
    title: 'Risk Mitigation',
    desc: `Rollback strategies, validation frameworks, and parallel testing methodologies. How to achieve ${platform.firstBootSuccess} first-boot success rates on every migration.`,
    accent: '#8b5cf6',
  },
  {
    number: '04',
    title: 'Real Results',
    desc: 'Three enterprise case studies with detailed savings data: a financial services firm ($1.2M/yr), a healthcare provider ($720K/yr), and a media company ($890K/yr).',
    accent: '#22c55e',
  },
];

const otherResources = [
  {
    title: 'ROI Calculator',
    desc: 'Calculate your projected savings from migrating off VMware with our interactive tool.',
    link: '/roi',
  },
  {
    title: 'Technical Brief',
    desc: 'Deep dive into HyperSDK Platform architecture: hexagonal design, provider plugins, and REST API.',
    link: '/docs/intro',
  },
  {
    title: 'Migration Checklist',
    desc: 'Pre-migration, during, and post-migration steps for enterprise VM migrations.',
    link: '/blog/migration-checklist',
  },
];

const roles = [
  'Select your role',
  'VP / Director of Infrastructure',
  'CTO / CIO',
  'Systems Engineer',
  'DevOps / Platform Engineer',
  'IT Manager',
  'Other',
];

export default function Whitepaper(): ReactNode {
  const {status, submit, error, mailHint} = useFormspree();
  const [form, setForm] = useState({name: '', email: '', company: '', role: roles[1]});

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    captureMarketingAttribution();
    const fd = new FormData(e.currentTarget);
    const attribution = getMarketingAttribution();
    Object.entries(attribution).forEach(([key, value]) => fd.set(key, value));
    const ok = await submit(fd);
    if (ok) {
      dispatchMarketingEvent('whitepaper_download', {source: 'vmware-exit-guide'});
    }
  };

  const submitted = status === 'done' || status === 'done_no_mail';

  return (
    <ProductPage
      title="Download: The Complete VMware Exit Guide"
      description="Download the VMware Exit Guide. Learn how Fortune 500 companies saved $1.2M/year migrating from VMware to KVM with HyperSDK Platform."
    >
      <MarketingHero pageId="whitepaper" />

      <PageContent>
        {/* Metadata bar */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            gap: '2rem',
            marginBottom: '3rem',
            flexWrap: 'wrap',
          }}
        >
          {[
            {label: '48 pages', icon: '\u{1F4C4}'},
            {label: '25 min read', icon: '\u{23F1}'},
            {label: '4 chapters', icon: '\u{1F4D6}'},
            {label: '3 case studies', icon: '\u{1F4CA}'},
          ].map((m) => (
            <div
              key={m.label}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                background: 'rgba(255, 255, 255, 0.03)',
                border: '1px solid rgba(255, 255, 255, 0.06)',
                borderRadius: 8,
                padding: '0.5rem 1rem',
              }}
            >
              <span style={{fontSize: '1rem'}}>{m.icon}</span>
              <span
                style={{
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: '0.8rem',
                  fontWeight: 600,
                  color: 'var(--hs-text-muted)',
                }}
              >
                {m.label}
              </span>
            </div>
          ))}
        </div>

        <div
          className={styles.splitGrid}
          style={{
            marginBottom: '5rem',
          }}
        >
          {/* What's Inside */}
          <div>
            <h2
              style={{
                fontSize: '1.6rem',
                fontWeight: 700,
                color: 'var(--hs-text-heading)',
                marginBottom: '1.5rem',
              }}
            >
              What's Inside
            </h2>
            <ul
              style={{listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '1rem'}}
            >
              {insidePoints.map((point) => (
                <li
                  key={point}
                  className={styles.featureCard}
                  style={{
                    padding: '1rem 1.25rem',
                    paddingLeft: '2.5rem',
                    position: 'relative',
                  }}
                >
                  <span
                    style={{
                      position: 'absolute',
                      left: '1rem',
                      top: '1rem',
                      color: 'var(--hs-accent-light)',
                      fontWeight: 700,
                    }}
                  >
                    {'\u2713'}
                  </span>
                  <span style={{color: 'var(--hs-text-body)', fontSize: '0.95rem', lineHeight: 1.6}}>{point}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Form */}
          <div
            className={styles.featureCard}
            style={{
              border: '1px solid rgba(255, 140, 0, 0.15)',
              padding: '2.5rem',
            }}
          >
            {submitted ? (
              <div style={{textAlign: 'center', padding: '2rem 0'}}>
                <div style={{fontSize: '3rem', marginBottom: '1rem'}}>{'\u2705'}</div>
                <h3
                  style={{
                    color: 'var(--hs-text-heading)',
                    fontSize: '1.5rem',
                    fontWeight: 700,
                    marginBottom: '0.75rem',
                  }}
                >
                  Thank you!
                </h3>
                <p style={{color: 'var(--hs-text-muted)', fontSize: '1rem', lineHeight: 1.7}}>
                  {status === 'done_no_mail'
                    ? `We saved your request. Email delivery failed — contact ${EMAIL_INFO} for the VMware Exit Guide.${mailHint ? ` ${mailHint}` : ''}`
                    : 'Our team will send the VMware Exit Guide within one business day. Check your inbox for a reply from Zyvor.'}
                </p>
              </div>
            ) : (
              <>
                <h3
                  style={{color: 'var(--hs-text-heading)', fontSize: '1.3rem', fontWeight: 700, marginBottom: '1.5rem'}}
                >
                  Get Your Free Copy
                </h3>
                <form onSubmit={handleSubmit} style={{display: 'flex', flexDirection: 'column', gap: '1rem'}}>
                  <input type="hidden" name="_intent" value="sales" />
                  <input type="hidden" name="_subject" value="VMware Exit Guide download request" />
                  <input type="hidden" name="source" value="whitepaper" />
                  <input
                    type="hidden"
                    name="message"
                    value="Please send the VMware Exit Guide whitepaper (48-page PDF)."
                  />
                  {[
                    {label: 'Full Name', key: 'name', type: 'text', placeholder: 'Jane Smith'},
                    {label: 'Work Email', key: 'email', type: 'email', placeholder: 'jane@company.com'},
                    {label: 'Company', key: 'company', type: 'text', placeholder: 'Acme Corp'},
                  ].map((field) => (
                    <div key={field.key}>
                      <label
                        className={styles.monoLabel}
                        style={{
                          display: 'block',
                          color: 'var(--hs-text-muted)',
                          fontSize: '0.8rem',
                          marginBottom: '0.4rem',
                          letterSpacing: '0.05em',
                        }}
                      >
                        {field.label}
                      </label>
                      <input
                        type={field.type}
                        name={field.key}
                        placeholder={field.placeholder}
                        required
                        value={form[field.key as keyof typeof form]}
                        onChange={(e) => setForm({...form, [field.key]: e.target.value})}
                        style={{
                          width: '100%',
                          padding: '0.75rem 1rem',
                          background: 'rgba(0, 0, 0, 0.4)',
                          border: '1px solid rgba(255, 255, 255, 0.1)',
                          borderRadius: 8,
                          color: 'var(--hs-text-heading)',
                          fontSize: '0.95rem',
                          outline: 'none',
                          boxSizing: 'border-box',
                        }}
                      />
                    </div>
                  ))}
                  <div>
                    <label
                      className={styles.monoLabel}
                      style={{
                        display: 'block',
                        color: 'var(--hs-text-muted)',
                        fontSize: '0.8rem',
                        marginBottom: '0.4rem',
                        letterSpacing: '0.05em',
                      }}
                    >
                      Role
                    </label>
                    <select
                      required
                      name="role"
                      value={form.role}
                      onChange={(e) => setForm({...form, role: e.target.value})}
                      style={{
                        width: '100%',
                        padding: '0.75rem 1rem',
                        background: 'rgba(0, 0, 0, 0.4)',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                        borderRadius: 8,
                        color: 'var(--hs-text-heading)',
                        fontSize: '0.95rem',
                        outline: 'none',
                        boxSizing: 'border-box',
                      }}
                    >
                      {roles.map((r, i) => (
                        <option key={r} value={r} disabled={i === 0}>
                          {r}
                        </option>
                      ))}
                    </select>
                  </div>
                  <button
                    type="submit"
                    className={styles.primaryBtn}
                    disabled={status === 'sending'}
                    style={{
                      marginTop: '0.5rem',
                      justifyContent: 'center',
                    }}
                  >
                    {status === 'sending' ? 'Sending…' : 'Download Now'}
                  </button>
                  {status === 'error' && <p style={{color: '#ef4444', fontSize: '0.9rem', margin: 0}}>{error}</p>}
                </form>
              </>
            )}
          </div>
        </div>

        {/* Chapter Preview */}
        <SectionHeader
          eyebrow="Chapter Preview"
          title="What You Will Learn"
          subtitle="Four chapters covering every aspect of a successful VMware exit strategy."
        />
        <div className={styles.gridCol2} style={{gap: '1.5rem', marginBottom: '5rem'}}>
          {chapters.map((ch) => (
            <div
              key={ch.number}
              className={styles.featureCard}
              style={{
                padding: '2rem',
                position: 'relative',
                overflow: 'hidden',
              }}
            >
              {/* Chapter number accent */}
              <div
                style={{
                  position: 'absolute',
                  top: -8,
                  right: -4,
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: '5rem',
                  fontWeight: 800,
                  color: ch.accent,
                  opacity: 0.06,
                  lineHeight: 1,
                }}
              >
                {ch.number}
              </div>

              <div
                style={{
                  display: 'inline-block',
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: '0.7rem',
                  fontWeight: 700,
                  color: ch.accent,
                  background: `${ch.accent}15`,
                  border: `1px solid ${ch.accent}30`,
                  borderRadius: 6,
                  padding: '0.15rem 0.6rem',
                  marginBottom: '0.75rem',
                  letterSpacing: '0.06em',
                }}
              >
                Chapter {ch.number}
              </div>

              <h3
                style={{
                  color: 'var(--hs-text-heading)',
                  fontSize: '1.15rem',
                  fontWeight: 700,
                  marginBottom: '0.5rem',
                }}
              >
                {ch.title}
              </h3>
              <p
                style={{
                  color: 'var(--hs-text-muted)',
                  fontSize: '0.9rem',
                  lineHeight: 1.7,
                  margin: 0,
                }}
              >
                {ch.desc}
              </p>
            </div>
          ))}
        </div>

        {/* Other Resources */}
        <h2
          style={{
            fontSize: '1.8rem',
            fontWeight: 800,
            color: 'var(--hs-text-heading)',
            textAlign: 'center',
            marginBottom: '2rem',
          }}
        >
          Other Resources
        </h2>
        <div
          className={styles.gridCol3}
          style={{
            marginBottom: '4rem',
          }}
        >
          {otherResources.map((r) => (
            <Link key={r.title} to={r.link} style={{textDecoration: 'none'}}>
              <div className={styles.featureCard} style={{height: '100%'}}>
                <h3
                  style={{
                    color: 'var(--hs-accent-light)',
                    fontSize: '1.1rem',
                    fontWeight: 700,
                    marginBottom: '0.75rem',
                  }}
                >
                  {r.title}
                </h3>
                <p className={styles.featureCardDesc}>{r.desc}</p>
              </div>
            </Link>
          ))}
        </div>

        <CTASection
          title="Ready to plan your VMware exit?"
          subtitle="Talk to solutions engineering about your VM estate, timeline, and savings model."
          primaryCta={{label: 'Schedule assessment', to: '/contact?intent=vmware-exit', event: 'cta_click'}}
          secondaryCta={{label: 'Take the savings quiz', to: '/assessment'}}
        />
      </PageContent>
    </ProductPage>
  );
}
