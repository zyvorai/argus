// Copyright (c) 2026 ZyvorAI Labs Private Limited. All rights reserved.
// Proprietary software — see LICENSE in the repository root.
// https://zyvor.dev · info@zyvor.dev

import type {ReactNode} from 'react';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import {
  ProductPage,
  MarketingHero,
  PageContent,
  StatGrid,
  SectionHeader,
  FeatureGrid,
  FeaturePanels,
  CTASection,
  PillGroup,
  SupportOpenSourceSection,
  styles,
} from '../components/shared';
import {GITHUB_SPONSOR_URL} from '../data/open-source-links';
import {platform} from '../data/platform-stats';
import {LEGAL_ENTITY_INDIA} from '../data/legal-entity-india';
import {getAboutPageCopy} from '../data/about-locale';

const trustedTechnologies = [
  'KVM',
  'KubeVirt',
  'libvirt',
  'Kubernetes',
  'CDI',
  'qcow2',
  'OVA/OVF',
  'VMware vSphere',
  'Nutanix AHV',
];

const stats = [
  {label: 'Cloud providers', value: String(platform.cloudProviders)},
  {label: 'First-boot success', value: platform.firstBootSuccess},
  {label: 'Platform scope', value: 'Integrated'},
  {label: 'Hypervisor stack', value: 'KVM / KubeVirt'},
];

const values = [
  {
    title: 'Open Standards',
    desc: 'Build on KVM, libvirt, KubeVirt — no vendor lock-in. We believe infrastructure portability should be the default, not the exception.',
  },
  {
    title: 'Enterprise First',
    desc: 'Every feature designed for production workloads. From RBAC and audit logging to incremental exports and rollback, reliability is non-negotiable.',
  },
  {
    title: 'Developer Experience',
    desc: 'APIs, CLIs, and dashboards that engineers love — consistent interfaces for automation, operations, and day-2 VM management without toolchain sprawl.',
  },
  {
    title: 'Sustainability',
    desc: 'Carbon-aware scheduling by default. HyperSDK Platform optimizes migration timing based on grid carbon intensity, helping enterprises reduce their environmental footprint.',
  },
];

const timeline = [
  {
    year: '2026',
    label: 'Zeus OS platform',
    detail:
      'Zeus OS unifies migration (HyperSDK Platform), conversion (hyper2kvm), assurance (GuestKit), visual ops (Zeus OS), declarative VMs (Veyron), runtime portability (Aether), network intelligence (PacketWolf), GPU fabric (Forge), bare metal (IronWolf), and cluster bootstrap (HyperCluster) — one API fabric from VMware exit through KubeVirt day-2.',
  },
];

export default function About(): ReactNode {
  const {i18n} = useDocusaurusContext();
  const copy = getAboutPageCopy(i18n.currentLocale);

  return (
    <ProductPage
      title="About Us"
      description="Learn about Zyvor — HyperSDK Platform: Kubernetes-native VM migration, lifecycle management, and enterprise infrastructure portability."
    >
      <MarketingHero pageId="about" />

      <PageContent>
        {/* Mission & Vision */}
        <FeaturePanels
          panels={[
            {
              title: copy.missionTitle,
              items: [copy.missionBody],
            },
            {
              title: copy.visionTitle,
              items: [copy.visionBody],
            },
          ]}
        />

        {/* Our Story */}
        <SectionHeader eyebrow={copy.storyEyebrow} title={copy.storyTitle} />
        <div
          className={styles.featureCard}
          style={{
            maxWidth: 800,
            margin: '0 auto 5rem',
            padding: '2.5rem',
            border: '1px solid rgba(255, 140, 0, 0.12)',
          }}
        >
          <p
            style={{
              color: 'var(--hs-text-body)',
              fontSize: '1.05rem',
              lineHeight: 1.8,
              margin: 0,
            }}
          >
            Zyvor was born from a simple observation: enterprise VM migration was still painfully manual. After
            years of building enterprise infrastructure tools, our team set out to create the migration platform we
            always wished existed &mdash; one that handles the entire lifecycle from discovery to deployment. The
            customer-facing platform is <em>Zeus OS</em>; <em>HyperSDK Platform</em> is the migration engine inside it.
          </p>
          <p
            style={{
              color: 'var(--hs-text-muted)',
              fontSize: '1rem',
              lineHeight: 1.8,
              marginTop: '1.25rem',
              marginBottom: 0,
            }}
          >
            What started as a single-provider CLI tool has grown into an integrated infrastructure platform supporting{' '}
            {platform.cloudProviders} cloud providers &mdash; all built with the same principle: migrations should be
            predictable, repeatable, and risk-free.
          </p>
        </div>

        <SectionHeader
          eyebrow="Corporate registration"
          title="India (MCA)"
          subtitle="Legal entity behind the Zyvor brand. Current company particulars can be confirmed on the Ministry of Corporate Affairs website."
        />
        <div
          className={styles.featureCard}
          style={{
            maxWidth: 800,
            margin: '0 auto 5rem',
            padding: '2.5rem',
            border: '1px solid rgba(255, 140, 0, 0.12)',
          }}
        >
          <p style={{color: 'var(--hs-text-body)', fontSize: '1rem', lineHeight: 1.8, margin: 0}}>
            <strong style={{color: 'var(--hs-text-heading)'}}>{LEGAL_ENTITY_INDIA.tradeName}</strong> is the trade name
            of <strong style={{color: 'var(--hs-text-heading)'}}>{LEGAL_ENTITY_INDIA.legalName}</strong>, incorporated
            in India under the Companies Act, 2013. Corporate Identity Number (CIN):{' '}
            <span style={{fontFamily: "'JetBrains Mono', monospace", color: 'var(--hs-text-muted)'}}>
              {LEGAL_ENTITY_INDIA.cin}
            </span>
            .{' '}
            <a href={LEGAL_ENTITY_INDIA.mcaVerifyUrl} target="_blank" rel="noopener noreferrer">
              Verify on mca.gov.in
            </a>
            . Registered office: {LEGAL_ENTITY_INDIA.addressOneLine}.
          </p>
        </div>

        <SectionHeader
          eyebrow="Legal"
          title="Licensing & trademarks"
          subtitle="Proprietary suite products are licensed by ZyvorAI Labs Private Limited. GuestKit guest-inspection source is LGPL-3.0-or-later with Zyvor company terms on branded binaries."
        />
        <div
          className={styles.featureCard}
          style={{
            maxWidth: 800,
            margin: '0 auto 5rem',
            padding: '2.5rem',
            border: '1px solid rgba(255, 140, 0, 0.12)',
          }}
        >
          <p style={{color: 'var(--hs-text-body)', fontSize: '1rem', lineHeight: 1.8, margin: 0}}>
            Self-hosted deploy accepts the <a href="/license">proprietary deploy EULA</a>. Hosted platform use is
            governed by our <a href="/terms">Terms of Service</a> and <a href="/privacy">Privacy Policy</a>. See the{' '}
            <a href="/docs/licensing">licensing documentation</a> for tiers, product matrix, trademarks, and third-party
            policy. Enterprise programs: <a href="mailto:legal@zyvor.dev">legal@zyvor.dev</a>.
          </p>
        </div>

        {/* Key Numbers */}
        <StatGrid stats={stats} columns={4} />

        {/* Our Values */}
        <SectionHeader
          eyebrow={copy.valuesEyebrow}
          title={copy.valuesTitle}
          subtitle="Four principles that shape every decision we make, from architecture choices to customer interactions."
        />
        <FeatureGrid columns={2} features={values} />

        <SectionHeader
          eyebrow={copy.trustedEyebrow}
          title={copy.trustedTitle}
          subtitle="Open standards and proven infrastructure components underpinning portability, migration, and day-2 operations."
        />
        <div style={{marginBottom: '5rem'}}>
          <PillGroup items={trustedTechnologies} />
        </div>

        {/* By the Numbers — Timeline */}
        <SectionHeader eyebrow={copy.timelineEyebrow} title={copy.timelineTitle} />
        <div
          style={{
            maxWidth: 700,
            margin: '0 auto 5rem',
            position: 'relative',
            paddingLeft: '2.5rem',
          }}
        >
          {/* Vertical line */}
          <div
            style={{
              position: 'absolute',
              left: 8,
              top: 0,
              bottom: 0,
              width: 2,
              background: 'linear-gradient(to bottom, #f0583a, rgba(139, 92, 246, 0.3), transparent)',
            }}
          />

          {timeline.map((t, i) => (
            <div key={t.year} style={{marginBottom: i < timeline.length - 1 ? '2rem' : 0, position: 'relative'}}>
              {/* Dot */}
              <div
                style={{
                  position: 'absolute',
                  left: '-2.5rem',
                  top: '1.5rem',
                  width: 18,
                  height: 18,
                  borderRadius: '50%',
                  background: i === timeline.length - 1 ? '#f0583a' : 'rgba(240, 88, 58, 0.3)',
                  border:
                    i === timeline.length - 1 ? '3px solid rgba(240, 88, 58, 0.4)' : '2px solid rgba(240, 88, 58, 0.2)',
                  transform: 'translateX(-50%)',
                  marginLeft: 9,
                }}
              />

              <div
                className={styles.featureCard}
                style={{
                  border: i === timeline.length - 1 ? '1px solid rgba(240, 88, 58, 0.2)' : undefined,
                }}
              >
                <div style={{display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.5rem'}}>
                  <span
                    style={{
                      fontFamily: "'JetBrains Mono', monospace",
                      fontSize: '1.1rem',
                      fontWeight: 700,
                      color: 'var(--hs-accent)',
                    }}
                  >
                    {t.year}
                  </span>
                  {i === timeline.length - 1 && (
                    <span
                      style={{
                        background: 'rgba(240, 88, 58, 0.15)',
                        color: 'var(--hs-accent)',
                        fontSize: '0.7rem',
                        fontWeight: 600,
                        textTransform: 'uppercase',
                        letterSpacing: '0.08em',
                        padding: '0.2rem 0.6rem',
                        borderRadius: 6,
                      }}
                    >
                      Now
                    </span>
                  )}
                </div>
                <h4
                  style={{
                    color: 'var(--hs-text-heading)',
                    fontSize: '1.05rem',
                    fontWeight: 600,
                    marginBottom: '0.4rem',
                  }}
                >
                  {t.label}
                </h4>
                <p style={{color: 'var(--hs-text-muted)', fontSize: '0.9rem', lineHeight: 1.7, margin: 0}}>
                  {t.detail}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* Team */}
        <SectionHeader
          eyebrow="Our Team"
          title="Built for Enterprise Infrastructure Teams"
          subtitle="Our team combines deep expertise in virtualization, cloud infrastructure, and systems programming. We have spent years building and operating large-scale VM environments, and we channel that experience into making HyperSDK Platform the most reliable migration platform available."
        />
        <FeatureGrid
          columns={3}
          features={[
            {
              title: 'Platform Engineering',
              desc: 'Core migration engine, provider integrations, and API development in Go.',
            },
            {
              title: 'Frontend & Dashboard',
              desc: 'React and TypeScript dashboards for migration workflows, fleet visibility, and day-2 operations across the platform.',
            },
            {
              title: 'Infrastructure & DevOps',
              desc: 'CI/CD, deployment automation, and reliability engineering across all environments.',
            },
          ]}
        />

        {/* Leadership */}
        <SectionHeader
          eyebrow="Leadership"
          title="Co-Founders & engineering leadership"
          subtitle="Zyvor builds HyperSDK Platform — portable virtualization and Kubernetes-native operations without vendor lock-in."
        />
        <div
          className={styles.featureCard}
          style={{
            maxWidth: 800,
            margin: '0 auto 4rem',
            padding: '2.5rem',
            border: '1px solid rgba(255, 140, 0, 0.12)',
          }}
        >
          <h3
            style={{
              color: 'var(--hs-text-heading)',
              fontSize: '1.25rem',
              fontWeight: 700,
              marginBottom: '0.35rem',
            }}
          >
            Susant Sahani
          </h3>
          <p
            style={{
              color: 'var(--hs-text-muted)',
              fontSize: '0.9rem',
              marginBottom: '1.25rem',
              marginTop: 0,
              letterSpacing: '0.02em',
            }}
          >
            Founder &amp; CEO at Zyvor
          </p>
          <p
            style={{
              color: 'var(--hs-text-body)',
              fontSize: '1.05rem',
              lineHeight: 1.8,
              margin: '0 0 1.25rem',
            }}
          >
            Susant Sahani is Founder &amp; CEO of{' '}
            <a href="https://zyvor.dev" target="_blank" rel="noopener noreferrer">
              <strong style={{color: 'var(--hs-text-heading)'}}>Zyvor</strong>
            </a>{' '}
            and architect of <strong style={{color: 'var(--hs-text-heading)'}}>HyperSDK Platform</strong> — focused on
            infrastructure portability, VMware modernization, and Kubernetes-native virtualization.
          </p>
          <p
            style={{
              color: 'var(--hs-text-body)',
              fontSize: '1.05rem',
              lineHeight: 1.8,
              margin: '0 0 1.25rem',
            }}
          >
            He previously worked at Red Hat as a Principal Software Engineer and held engineering roles at VMware,
            Broadcom, and Armada, building large-scale Linux, virtualization, and distributed infrastructure systems.
          </p>
          <p
            style={{
              color: 'var(--hs-text-body)',
              fontSize: '1.05rem',
              lineHeight: 1.8,
              margin: '0 0 1.25rem',
            }}
          >
            He is an upstream contributor within the systemd ecosystem, with work spanning systemd-networkd, journaling,
            service management, networking, and Linux userspace internals. His contributions focus on operational
            reliability, networking infrastructure, logging systems, and modern Linux platform engineering.
          </p>
          <p
            style={{
              color: 'var(--hs-text-body)',
              fontSize: '1.05rem',
              lineHeight: 1.8,
              margin: 0,
            }}
          >
            GitHub recognitions include{' '}
            <strong style={{color: 'var(--hs-text-heading)'}}>Arctic Code Vault Contributor</strong>, reflecting
            sustained work across major open-source infrastructure repositories.
          </p>

          <p
            style={{
              color: 'var(--hs-text-heading)',
              fontSize: '0.85rem',
              fontWeight: 700,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              marginTop: '1.75rem',
              marginBottom: '0.65rem',
              fontFamily: "'JetBrains Mono', monospace",
            }}
          >
            systemd & upstream
          </p>
          <ul className={styles.featureCardList} style={{marginBottom: '1rem'}}>
            <li>
              <a href="https://github.com/systemd/systemd" target="_blank" rel="noopener noreferrer">
                systemd/systemd
              </a>
            </li>
            <li>
              <a
                href="https://github.com/systemd/systemd/tree/main/src/network"
                target="_blank"
                rel="noopener noreferrer"
              >
                systemd-networkd
              </a>
            </li>
            <li>
              <a href="https://github.com/systemd/systemd-netlogd" target="_blank" rel="noopener noreferrer">
                systemd/systemd-netlogd
              </a>
            </li>
          </ul>

          <p style={{color: 'var(--hs-text-muted)', fontSize: '0.95rem', marginTop: '1rem', marginBottom: 0}}>
            <a
              href="https://github.com/ssahani"
              target="_blank"
              rel="noopener noreferrer"
              style={{color: 'var(--hs-accent-light)', fontWeight: 600}}
            >
              GitHub
            </a>
            {' · '}
            <a
              href={GITHUB_SPONSOR_URL}
              target="_blank"
              rel="noopener noreferrer"
              style={{color: 'var(--hs-accent-light)', fontWeight: 600}}
            >
              GitHub Sponsors
            </a>
            {' · '}
            <a
              href="https://www.linkedin.com/in/susantsahani"
              target="_blank"
              rel="noopener noreferrer"
              style={{color: 'var(--hs-accent-light)', fontWeight: 600}}
            >
              LinkedIn
            </a>
            {' · '}
            <a
              href="https://zyvor.dev"
              target="_blank"
              rel="noopener noreferrer"
              style={{color: 'var(--hs-accent-light)', fontWeight: 600}}
            >
              zyvor.dev
            </a>
            {' · '}
            <a
              href="https://x.com/SusantSahani"
              target="_blank"
              rel="noopener noreferrer"
              style={{color: 'var(--hs-accent-light)', fontWeight: 600}}
            >
              @SusantSahani
            </a>
            {' · '}
            <a href="/contact" style={{color: 'var(--hs-accent-light)', fontWeight: 600}}>
              Contact
            </a>
          </p>
        </div>

        <div
          className={styles.featureCard}
          style={{
            maxWidth: 800,
            margin: '0 auto 4rem',
            padding: '2.5rem',
            border: '1px solid rgba(255, 140, 0, 0.12)',
          }}
        >
          <h3
            style={{
              color: 'var(--hs-text-heading)',
              fontSize: '1.25rem',
              fontWeight: 700,
              marginBottom: '0.35rem',
            }}
          >
            Amit Kumar
          </h3>
          <p
            style={{
              color: 'var(--hs-text-muted)',
              fontSize: '0.9rem',
              marginBottom: '1.25rem',
              marginTop: 0,
              letterSpacing: '0.02em',
            }}
          >
            Co-Founder at Zyvor
          </p>
          <p
            style={{
              color: 'var(--hs-text-body)',
              fontSize: '1.05rem',
              lineHeight: 1.8,
              margin: '0 0 1.25rem',
            }}
          >
            Amit Kumar is Co-Founder of{' '}
            <a href="https://zyvor.dev" target="_blank" rel="noopener noreferrer">
              <strong style={{color: 'var(--hs-text-heading)'}}>Zyvor</strong>
            </a>
            , where he is focused on building next-generation AI and infrastructure platforms that empower developers
            and enterprises worldwide.
          </p>
          <p
            style={{
              color: 'var(--hs-text-body)',
              fontSize: '1.05rem',
              lineHeight: 1.8,
              margin: '0 0 1.25rem',
            }}
          >
            With over 18 years of experience spanning Product Management, software engineering, and mobile architecture,
            he has led the design and delivery of large-scale solutions across mobile, web, cloud, and AI-driven
            systems.
          </p>
          <p
            style={{
              color: 'var(--hs-text-body)',
              fontSize: '1.05rem',
              lineHeight: 1.8,
              margin: '0 0 1.25rem',
            }}
          >
            His interests span agentic AI, on-device intelligence, virtualization, and enterprise infrastructure — with
            a vision to make advanced technology more accessible, scalable, and impactful.
          </p>
          <p
            style={{
              color: 'var(--hs-text-body)',
              fontSize: '1.05rem',
              lineHeight: 1.8,
              margin: 0,
            }}
          >
            He holds an <strong style={{color: 'var(--hs-text-heading)'}}>M.Tech from IIT Patna</strong>.
          </p>

          <p style={{color: 'var(--hs-text-muted)', fontSize: '0.95rem', marginTop: '1rem', marginBottom: 0}}>
            <a href="/contact" style={{color: 'var(--hs-accent-light)', fontWeight: 600}}>
              Contact
            </a>
          </p>
        </div>

        {/* Technology */}
        <SectionHeader eyebrow="Technology" title="Built with Modern Infrastructure Tools" />
        <FeatureGrid
          columns={3}
          features={[
            {
              title: 'Go',
              desc: 'High-performance backend with hexagonal architecture, multi-cloud provider integrations, and APIs built for migration automation at scale.',
            },
            {
              title: 'React',
              desc: 'Operational dashboards with real-time monitoring, migration workflows, and interactive orchestration builders.',
            },
            {
              title: 'TypeScript',
              desc: 'Type-safe frontend development with comprehensive component library and API client.',
            },
          ]}
        />

        <SupportOpenSourceSection compact />

        {/* CTA */}
        <CTASection
          title={copy.ctaTitle}
          subtitle={copy.ctaSubtitle}
          primaryCta={{label: copy.contactUs, to: '/contact?intent=sales'}}
          secondaryCta={{label: copy.scheduleDemo, to: '/contact?intent=demo'}}
        />
      </PageContent>
    </ProductPage>
  );
}
