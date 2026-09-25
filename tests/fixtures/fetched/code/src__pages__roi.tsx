// Copyright 2026 Zyvor AI Labs · https://zyvor.dev
// SPDX-License-Identifier: Apache-2.0

import {type ReactNode, useState, useCallback, useRef, useEffect} from 'react';
import Link from '@docusaurus/Link';
import {ProductPage, MarketingHero, PageContent, SectionHeader, CTASection, styles} from '../components/shared';
import {buildRoiContactUrl} from '../utils/roiContactPrefill';
import {dispatchMarketingEvent} from '../utils/marketingEvents';

const cloudStorage = [
  {provider: 'AWS S3', cost: '$0.023/GB', monthly: ''},
  {provider: 'Azure Blob', cost: '$0.018/GB', monthly: ''},
  {provider: 'Google Cloud Storage', cost: '$0.020/GB', monthly: ''},
  {provider: 'OCI Object Storage', cost: '$0.0255/GB', monthly: ''},
];

export default function ROICalculator(): ReactNode {
  const [vmCount, setVmCount] = useState(100);
  const [avgSize, setAvgSize] = useState(200);
  const [vmwareCost, setVmwareCost] = useState(1200);
  const [timeline, setTimeline] = useState(3);

  const currentAnnual = vmCount * vmwareCost;
  const hypersdkAnnual = vmCount * 100;
  const annualSavings = currentAnnual - hypersdkAnnual;
  const threeYearSavings = annualSavings * 3;
  const roiPercent = currentAnnual > 0 ? Math.round((annualSavings / currentAnnual) * 100) : 0;
  const paybackMonths =
    annualSavings > 0 ? Math.max(1, Math.round((hypersdkAnnual * (timeline / 12)) / (annualSavings / 12))) : 0;

  const [copied, setCopied] = useState(false);
  const [shared, setShared] = useState(false);
  const copyTimerRef = useRef<number>(undefined);
  const shareTimerRef = useRef<number>(undefined);
  useEffect(
    () => () => {
      if (copyTimerRef.current) clearTimeout(copyTimerRef.current);
      if (shareTimerRef.current) clearTimeout(shareTimerRef.current);
    },
    [],
  );

  useEffect(() => {
    const timer = window.setTimeout(() => {
      dispatchMarketingEvent('roi_calculated', {
        vm_count: vmCount,
        roi_percent: roiPercent,
        annual_savings: annualSavings,
      });
    }, 800);
    return () => clearTimeout(timer);
  }, [vmCount, avgSize, vmwareCost, timeline, roiPercent, annualSavings]);

  const handleCopyResults = useCallback(() => {
    const text = [
      'HyperSDK Platform ROI Calculator Results',
      '================================',
      `Number of VMs: ${vmCount.toLocaleString('en-US')}`,
      `Average VM Size: ${avgSize} GB`,
      `Current VMware Cost/VM/Year: $${vmwareCost.toLocaleString('en-US')}`,
      `Migration Timeline: ${timeline} months`,
      '',
      `Current Annual Cost: $${currentAnnual.toLocaleString('en-US')}`,
      `HyperSDK Platform Annual Cost: $${hypersdkAnnual.toLocaleString('en-US')}`,
      `Annual Savings: $${annualSavings.toLocaleString('en-US')}`,
      `3-Year Savings: $${threeYearSavings.toLocaleString('en-US')}`,
      `ROI: ${roiPercent}%`,
      `Payback Period: ${paybackMonths} months`,
      '',
      'Get a custom ROI analysis at https://zyvor.dev/contact',
    ].join('\n');

    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      copyTimerRef.current = window.setTimeout(() => setCopied(false), 2000);
    });
  }, [
    vmCount,
    avgSize,
    vmwareCost,
    timeline,
    currentAnnual,
    hypersdkAnnual,
    annualSavings,
    threeYearSavings,
    roiPercent,
    paybackMonths,
  ]);

  const handleShareResults = useCallback(() => {
    const savingsFmt =
      annualSavings >= 1000000 ? `$${(annualSavings / 1000000).toFixed(1)}M` : `$${(annualSavings / 1000).toFixed(0)}K`;
    const text = `Based on our ROI calculator, migrating ${vmCount.toLocaleString('en-US')} VMs could save ${savingsFmt} annually. Learn more at zyvor.dev/roi`;

    navigator.clipboard.writeText(text).then(() => {
      setShared(true);
      shareTimerRef.current = window.setTimeout(() => setShared(false), 2000);
    });
  }, [vmCount, annualSavings]);

  return (
    <ProductPage
      title="ROI Calculator"
      description="Calculate your migration savings with the HyperSDK Platform ROI calculator."
    >
      <MarketingHero pageId="roi" />

      <PageContent>
        {/* Calculator */}
        <div className={styles.calcGrid}>
          {/* Inputs */}
          <div className={styles.featureCard} style={{padding: '2.5rem'}}>
            <h3 className={styles.monoLabel} style={{marginBottom: '2rem'}}>
              Your Environment
            </h3>

            <div style={{display: 'flex', flexDirection: 'column', gap: '2rem'}}>
              {/* VM Count */}
              <div>
                <div className={styles.sliderRow}>
                  <label htmlFor="roi-vm-count" className={styles.sliderLabel}>
                    Number of VMs
                  </label>
                  <span className={styles.sliderValue}>{vmCount.toLocaleString('en-US')}</span>
                </div>
                <input
                  id="roi-vm-count"
                  type="range"
                  min={10}
                  max={5000}
                  step={10}
                  value={vmCount}
                  onChange={(e) => setVmCount(Number(e.target.value))}
                  aria-valuetext={`${vmCount.toLocaleString('en-US')} virtual machines`}
                  className={styles.rangeSlider}
                />
                <div className={styles.sliderMinMax}>
                  <span className={styles.sliderBound}>10</span>
                  <span className={styles.sliderBound}>5,000</span>
                </div>
              </div>

              {/* Avg VM Size */}
              <div>
                <div className={styles.sliderRow}>
                  <label htmlFor="roi-avg-size" className={styles.sliderLabel}>
                    Average VM Size (GB)
                  </label>
                  <span className={styles.sliderValue}>{avgSize} GB</span>
                </div>
                <input
                  id="roi-avg-size"
                  type="range"
                  min={50}
                  max={2000}
                  step={50}
                  value={avgSize}
                  onChange={(e) => setAvgSize(Number(e.target.value))}
                  aria-valuetext={`${avgSize} gigabytes`}
                  className={styles.rangeSlider}
                />
                <div className={styles.sliderMinMax}>
                  <span className={styles.sliderBound}>50 GB</span>
                  <span className={styles.sliderBound}>2,000 GB</span>
                </div>
              </div>

              {/* VMware Cost per VM */}
              <div>
                <div className={styles.sliderRow}>
                  <label htmlFor="roi-vmware-cost" className={styles.sliderLabel}>
                    Current VMware Cost per VM/Year
                  </label>
                  <span className={styles.sliderValue}>${vmwareCost.toLocaleString('en-US')}</span>
                </div>
                <input
                  id="roi-vmware-cost"
                  type="range"
                  min={200}
                  max={5000}
                  step={100}
                  value={vmwareCost}
                  onChange={(e) => setVmwareCost(Number(e.target.value))}
                  aria-valuetext={`$${vmwareCost.toLocaleString('en-US')} per VM per year`}
                  className={styles.rangeSlider}
                />
                <div className={styles.sliderMinMax}>
                  <span className={styles.sliderBound}>$200</span>
                  <span className={styles.sliderBound}>$5,000</span>
                </div>
              </div>

              {/* Timeline */}
              <div>
                <div className={styles.sliderRow}>
                  <label htmlFor="roi-timeline" className={styles.sliderLabel}>
                    Migration Timeline (Months)
                  </label>
                  <span className={styles.sliderValue}>{timeline} months</span>
                </div>
                <input
                  id="roi-timeline"
                  type="range"
                  min={1}
                  max={12}
                  step={1}
                  value={timeline}
                  onChange={(e) => setTimeline(Number(e.target.value))}
                  aria-valuetext={`${timeline} months`}
                  className={styles.rangeSlider}
                />
                <div className={styles.sliderMinMax}>
                  <span className={styles.sliderBound}>1 month</span>
                  <span className={styles.sliderBound}>12 months</span>
                </div>
              </div>
            </div>
          </div>

          {/* Outputs */}
          <div style={{display: 'flex', flexDirection: 'column', gap: '1.25rem'}}>
            {[
              {
                label: 'Current Annual Cost',
                value: `$${currentAnnual.toLocaleString('en-US')}`,
                color: 'var(--hs-error)',
                bg: 'rgba(239, 68, 68, 0.06)',
                border: 'rgba(239, 68, 68, 0.15)',
              },
              {
                label: 'HyperSDK Platform Annual Cost',
                value: `$${hypersdkAnnual.toLocaleString('en-US')}`,
                color: 'var(--hs-teal)',
                bg: 'rgba(16, 185, 129, 0.06)',
                border: 'rgba(16, 185, 129, 0.15)',
              },
              {
                label: 'Annual Savings',
                value: `$${annualSavings.toLocaleString('en-US')}`,
                color: 'var(--hs-accent-light)',
                bg: 'rgba(255, 140, 0, 0.06)',
                border: 'rgba(255, 140, 0, 0.15)',
              },
              {
                label: '3-Year Savings',
                value: `$${threeYearSavings.toLocaleString('en-US')}`,
                color: 'var(--hs-purple)',
                bg: 'rgba(167, 139, 250, 0.06)',
                border: 'rgba(167, 139, 250, 0.15)',
              },
              {
                label: 'ROI',
                value: `${roiPercent}%`,
                color: 'var(--hs-warning)',
                bg: 'rgba(245, 158, 11, 0.06)',
                border: 'rgba(245, 158, 11, 0.15)',
              },
              {
                label: 'Payback Period',
                value: `${paybackMonths} months`,
                color: 'var(--hs-info)',
                bg: 'rgba(6, 182, 212, 0.06)',
                border: 'rgba(6, 182, 212, 0.15)',
              },
            ].map((card) => (
              <div
                key={card.label}
                className={styles.roiResultCard}
                style={{
                  background: card.bg,
                  border: `1px solid ${card.border}`,
                }}
              >
                <span className={styles.roiResultLabel}>{card.label}</span>
                <span className={styles.roiResultValue} style={{color: card.color}}>
                  {card.value}
                </span>
              </div>
            ))}
            <button
              onClick={handleCopyResults}
              className={styles.secondaryBtn}
              style={{marginTop: '1rem', width: '100%', justifyContent: 'center'}}
            >
              {copied ? 'Copied!' : 'Copy Results'}
            </button>
            <button
              onClick={handleShareResults}
              className={styles.primaryBtn}
              style={{marginTop: '0.5rem', width: '100%', justifyContent: 'center', cursor: 'pointer'}}
            >
              {shared ? 'Summary Copied!' : 'Share Results'}
            </button>
          </div>
        </div>

        {/* Cloud Storage Comparison */}
        <SectionHeader
          eyebrow="Storage Costs"
          title="Cloud Storage Cost Comparison"
          subtitle={`Estimated monthly storage costs for your ${vmCount.toLocaleString('en-US')} VMs at ${avgSize} GB average.`}
        />

        <div className={styles.gridCol4}>
          {cloudStorage.map((cs) => {
            const monthlyCost = vmCount * avgSize * parseFloat(cs.cost.replace(/\$/g, '').replace(/\/GB/g, ''));
            return (
              <div key={cs.provider} className={styles.featureCard} style={{textAlign: 'center'}}>
                <h3 className={styles.featureCardTitle}>{cs.provider}</h3>
                <div
                  style={{
                    color: 'var(--hs-accent-light)',
                    fontFamily: 'var(--hs-font-mono)',
                    fontSize: '0.85rem',
                    marginBottom: '1rem',
                  }}
                >
                  {cs.cost}/month
                </div>
                <div
                  style={{
                    fontSize: '1.5rem',
                    fontWeight: 800,
                    color: 'var(--hs-text-heading)',
                    fontFamily: 'var(--hs-font-mono)',
                  }}
                >
                  ${monthlyCost.toLocaleString('en-US', {maximumFractionDigits: 0})}
                </div>
                <div className={styles.resultLabel}>estimated monthly</div>
              </div>
            );
          })}
        </div>

        {/* Real Example */}
        <SectionHeader
          eyebrow="Real User Data"
          title="Real Example: 500-VM Enterprise"
          subtitle="A financial services company migrated 500 VMs from VMware Cloud Foundation to KVM with RHEL subscriptions. Here are their actual numbers."
        />
        <div className={styles.gridCol4} style={{marginBottom: '1.5rem'}}>
          {[
            {
              label: 'Before (VMware)',
              value: '$1.2M/yr',
              color: 'var(--hs-error)',
              bg: 'rgba(239, 68, 68, 0.06)',
              border: 'rgba(239, 68, 68, 0.15)',
            },
            {
              label: 'After (KVM + RHEL)',
              value: '$96K/yr',
              color: 'var(--hs-teal)',
              bg: 'rgba(16, 185, 129, 0.06)',
              border: 'rgba(16, 185, 129, 0.15)',
            },
            {
              label: 'Annual Savings',
              value: '$1.1M/yr',
              color: 'var(--hs-accent-light)',
              bg: 'rgba(255, 140, 0, 0.06)',
              border: 'rgba(255, 140, 0, 0.15)',
            },
            {
              label: 'Payback Period',
              value: '2 months',
              color: 'var(--hs-info)',
              bg: 'rgba(6, 182, 212, 0.06)',
              border: 'rgba(6, 182, 212, 0.15)',
            },
          ].map((card) => (
            <div
              key={card.label}
              className={styles.roiResultCard}
              style={{
                background: card.bg,
                border: `1px solid ${card.border}`,
                borderRadius: 16,
                padding: '2rem',
                flexDirection: 'column',
                textAlign: 'center',
              }}
            >
              <div
                className={styles.roiResultValue}
                style={{
                  color: card.color,
                  fontSize: '2rem',
                  marginBottom: '0.5rem',
                }}
              >
                {card.value}
              </div>
              <div className={styles.resultLabel}>{card.label}</div>
            </div>
          ))}
        </div>
        <div className={styles.textCenter} style={{marginBottom: '4rem'}}>
          <p style={{color: 'var(--hs-text-subtle)', fontSize: '0.85rem', fontStyle: 'italic'}}>
            92% cost reduction. Full payback in under 60 days.
          </p>
        </div>

        {/* Savings by VM Count */}
        <SectionHeader
          eyebrow="Savings by Scale"
          title="3-Year Savings by VM Count"
          subtitle="Based on real user data across deployments of all sizes. Payback period: 1-3 months."
        />
        <div className={`${styles.featureGrid} ${styles.featureGridCol3}`} style={{marginBottom: '1.5rem'}}>
          {[
            {vms: '25 VMs', savings: '$112K', color: 'var(--hs-teal)'},
            {vms: '100 VMs', savings: '$730K', color: 'var(--hs-accent-light)'},
            {vms: '500 VMs', savings: '$3.74M', color: 'var(--hs-purple)'},
          ].map((row) => (
            <div key={row.vms} className={styles.featureCard} style={{textAlign: 'center'}}>
              <div className={styles.resultLabel}>{row.vms}</div>
              <div
                style={{
                  fontSize: '2.5rem',
                  fontWeight: 800,
                  color: row.color,
                  fontFamily: 'var(--hs-font-mono)',
                  marginBottom: '0.25rem',
                }}
              >
                {row.savings}
              </div>
              <div style={{color: 'var(--hs-text-subtle)', fontSize: '0.85rem'}}>over 3 years</div>
            </div>
          ))}
        </div>
        <div className={styles.textCenter} style={{marginBottom: '4rem'}}>
          <p style={{color: 'var(--hs-accent-light)', fontSize: '1rem', fontWeight: 600}}>
            Average payback period: 1-3 months. 70% average TCO reduction.
          </p>
        </div>

        {/* CTA */}
        <CTASection
          title="Get a Custom ROI Analysis"
          subtitle="Based on real user data. Average VMware licensing costs range from $5,000-$15,000 per socket. Our solutions engineers can analyze your specific environment and provide a detailed, auditable ROI report."
          primaryCta={{
            label: 'Get a Custom ROI Analysis',
            to: buildRoiContactUrl({vmCount, annualSavings, vmwareCost: currentAnnual}),
            event: 'roi_contact_click',
          }}
          secondaryCta={{
            label: 'Book a Demo',
            to: `/contact?intent=demo&vm_count=${vmCount}`,
            event: 'roi_contact_click',
          }}
        />
      </PageContent>
    </ProductPage>
  );
}
