// Copyright (c) 2026 ZyvorAI Labs Private Limited. All rights reserved.
// Proprietary software — see LICENSE in the repository root.
// https://zyvor.dev · info@zyvor.dev

import {useState, type ReactNode, type CSSProperties} from 'react';
import {ProductPage, PageContent} from '../components/shared';
import RazorpayButton from '../components/RazorpayButton';

const field: CSSProperties = {
  width: '100%',
  padding: '0.7rem 1rem',
  borderRadius: 8,
  border: '1px solid var(--hs-border)',
  backgroundColor: 'var(--hs-surface-code, #101722)',
  color: 'var(--hs-text-heading)',
  fontSize: '0.95rem',
  outline: 'none',
  boxSizing: 'border-box',
};

const label: CSSProperties = {
  display: 'block',
  fontSize: '0.8rem',
  color: 'var(--hs-text-muted)',
  marginBottom: '0.35rem',
};

export default function Pay(): ReactNode {
  const [amount, setAmount] = useState('');
  const [product, setProduct] = useState('');
  const [desc, setDesc] = useState('');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [licenceKey, setLicenceKey] = useState('');
  const [paymentId, setPaymentId] = useState('');
  const [invoiceUrl, setInvoiceUrl] = useState('');

  const paise = Math.round(parseFloat(amount || '0') * 100);
  const valid = paise >= 100 && product.trim().length > 0 && name.trim().length > 0 && email.trim().includes('@');

  function handleSuccess(pid: string, key?: string, _email?: string, inv?: string) {
    setPaymentId(pid);
    setLicenceKey(key ?? '');
    setInvoiceUrl(inv ?? '');
  }

  return (
    <ProductPage
      title="Make a Payment"
      description="Pay securely via Razorpay for any HyperSDK product, service, or invoice."
    >
      <PageContent>
        <div
          style={{
            maxWidth: 520,
            margin: '0 auto',
            background: 'var(--hs-surface)',
            border: '1px solid var(--hs-border)',
            borderRadius: 16,
            padding: '2.5rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '1.25rem',
          }}
        >
          <h2
            style={{
              fontSize: '1.25rem',
              fontWeight: 700,
              color: 'var(--hs-text-heading)',
              margin: 0,
            }}
          >
            Payment Details
          </h2>

          {paymentId ? (
            <div
              style={{
                background: 'rgba(34,197,94,0.08)',
                border: '1px solid rgba(34,197,94,0.25)',
                borderRadius: 12,
                padding: '1.5rem',
                textAlign: 'center',
              }}
            >
              <div style={{fontSize: '2rem', marginBottom: '0.5rem'}}>✓</div>
              <p style={{color: '#4ade80', fontWeight: 700, fontSize: '1.1rem', margin: '0 0 0.5rem'}}>
                Payment Successful
              </p>
              <p style={{color: 'var(--hs-text-muted)', fontSize: '0.85rem', margin: '0 0 1rem'}}>
                Payment ID: <code style={{color: 'var(--hs-text-heading)'}}>{paymentId}</code>
              </p>
              {licenceKey && (
                <div
                  style={{
                    background: 'var(--hs-surface-code, #101722)',
                    border: '1px solid var(--hs-border)',
                    borderRadius: 8,
                    padding: '0.75rem 1rem',
                    marginTop: '0.75rem',
                  }}
                >
                  <p style={{color: 'var(--hs-text-muted)', fontSize: '0.75rem', margin: '0 0 0.4rem'}}>Licence Key</p>
                  <code style={{color: '#4ade80', fontSize: '0.85rem', wordBreak: 'break-all'}}>{licenceKey}</code>
                </div>
              )}
              {invoiceUrl && (
                <a
                  href={invoiceUrl}
                  download
                  style={{
                    display: 'inline-block',
                    marginTop: '0.75rem',
                    padding: '0.5rem 1rem',
                    background: 'rgba(240,88,58,0.1)',
                    border: '1px solid rgba(240,88,58,0.3)',
                    borderRadius: 8,
                    color: 'var(--hs-accent)',
                    fontSize: '0.85rem',
                    fontWeight: 600,
                    textDecoration: 'none',
                  }}
                >
                  ↓ Download GST Invoice (PDF)
                </a>
              )}
            </div>
          ) : (
            <>
              <div>
                <label htmlFor="pay-amount" style={label}>
                  Amount (₹) <span style={{color: 'var(--hs-accent)'}}>*</span>
                </label>
                <input
                  id="pay-amount"
                  type="number"
                  min="1"
                  step="0.01"
                  placeholder="e.g. 590"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  style={field}
                  autoComplete="off"
                />
              </div>

              <div>
                <label htmlFor="pay-product" style={label}>
                  Product / Service <span style={{color: 'var(--hs-accent)'}}>*</span>
                </label>
                <input
                  id="pay-product"
                  type="text"
                  placeholder="e.g. ZySign Licence, Consulting, Invoice #42"
                  value={product}
                  onChange={(e) => setProduct(e.target.value)}
                  style={field}
                  autoComplete="off"
                />
              </div>

              <div>
                <label htmlFor="pay-desc" style={label}>
                  Description (optional)
                </label>
                <input
                  id="pay-desc"
                  type="text"
                  placeholder="Additional details"
                  value={desc}
                  onChange={(e) => setDesc(e.target.value)}
                  style={field}
                  autoComplete="off"
                />
              </div>

              <div style={{borderTop: '1px solid var(--hs-border)', paddingTop: '1rem'}}>
                <p style={{color: 'var(--hs-text-muted)', fontSize: '0.8rem', margin: '0 0 1rem'}}>
                  Required for GST receipt & email confirmation
                </p>

                <div style={{display: 'flex', flexDirection: 'column', gap: '1rem'}}>
                  <div>
                    <label htmlFor="pay-name" style={label}>
                      Full Name <span style={{color: 'var(--hs-accent)'}}>*</span>
                    </label>
                    <input
                      id="pay-name"
                      type="text"
                      placeholder="Your name"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      style={field}
                      autoComplete="name"
                    />
                  </div>

                  <div>
                    <label htmlFor="pay-email" style={label}>
                      Email <span style={{color: 'var(--hs-accent)'}}>*</span>
                    </label>
                    <input
                      id="pay-email"
                      type="email"
                      placeholder="your@email.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      style={field}
                      autoComplete="email"
                    />
                  </div>
                </div>
              </div>

              {valid && (
                <div
                  style={{
                    background: 'rgba(240,88,58,0.06)',
                    border: '1px solid rgba(240,88,58,0.2)',
                    borderRadius: 8,
                    padding: '0.75rem 1rem',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <span style={{color: 'var(--hs-text-muted)', fontSize: '0.85rem'}}>{product}</span>
                  <span style={{color: 'var(--hs-accent)', fontWeight: 700, fontSize: '1.1rem'}}>
                    ₹{parseFloat(amount).toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                  </span>
                </div>
              )}

              <RazorpayButton
                amount={paise}
                currency="INR"
                productName={product || 'Payment'}
                description={desc || product || 'Zyvor'}
                customerName={name}
                customerEmail={email}
                onSuccess={handleSuccess}
                style={{
                  width: '100%',
                  padding: '0.85rem',
                  borderRadius: 10,
                  border: 'none',
                  background: valid ? 'var(--hs-accent)' : 'rgba(255,255,255,0.08)',
                  color: valid ? '#fff' : 'var(--hs-text-muted)',
                  fontWeight: 700,
                  fontSize: '1rem',
                  cursor: valid ? 'pointer' : 'not-allowed',
                  transition: 'background 0.2s',
                  pointerEvents: valid ? 'auto' : 'none',
                }}
              >
                {valid ? `Pay ₹${parseFloat(amount).toLocaleString('en-IN')}` : 'Enter amount & product'}
              </RazorpayButton>

              <p style={{color: 'var(--hs-text-muted)', fontSize: '0.75rem', textAlign: 'center', margin: 0}}>
                Secured by Razorpay · All major cards, UPI, Net Banking accepted
              </p>
            </>
          )}
        </div>
      </PageContent>
    </ProductPage>
  );
}
