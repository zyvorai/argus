// Copyright (c) 2026 ZyvorAI Labs Private Limited. All rights reserved.
// Proprietary software — see LICENSE in the repository root.
// https://zyvor.dev · info@zyvor.dev

import {useEffect, useState, type ReactNode} from 'react';
import Link from '@docusaurus/Link';
import {ProductPage, PageContent, PageHero, SectionHeader, CTASection} from '../../components/shared';
import {
  computeSubscriberMilestones,
  formatPublishedDate,
  formatYouTubeCount,
  type YouTubePublicPayload,
  type YouTubeVideo,
} from '../../data/youtube-public';
import styles from './youtube.module.css';

function VideoGrid({videos}: {videos: YouTubeVideo[]}) {
  if (!videos.length) {
    return <div className={styles.emptyState}>No videos in this section yet.</div>;
  }
  return (
    <div className={styles.videoGrid}>
      {videos.map((video) => (
        <article key={video.id} className={styles.videoCard}>
          <a href={video.watchUrl} target="_blank" rel="noopener noreferrer" className={styles.thumbWrap}>
            <img src={video.thumbnailUrl} alt="" className={styles.thumb} loading="lazy" />
          </a>
          <div className={styles.videoBody}>
            <h3 className={styles.videoTitle}>
              <a
                href={video.watchUrl}
                target="_blank"
                rel="noopener noreferrer"
                style={{color: 'inherit', textDecoration: 'none'}}
              >
                {video.title}
              </a>
            </h3>
            <div className={styles.videoMeta}>
              <span>{formatYouTubeCount(video.viewCount)} views</span>
              <span>{formatYouTubeCount(video.likeCount)} likes</span>
              <span>{formatYouTubeCount(video.commentCount)} comments</span>
              <span>{formatPublishedDate(video.publishedAt)}</span>
            </div>
          </div>
        </article>
      ))}
    </div>
  );
}

export default function YouTubeAnalyticsPage(): ReactNode {
  const [data, setData] = useState<YouTubePublicPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch('/api/v1/youtube/public');
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const json = (await res.json()) as YouTubePublicPayload;
        if (!cancelled) setData(json);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load YouTube stats');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const channel = data?.channel;
  const milestones = computeSubscriberMilestones(data?.subscriberHistory);

  return (
    <ProductPage
      title="YouTube Growth"
      description="Public channel stats for Zyvor on YouTube — subscribers, views, latest demos, and migration content performance."
    >
      <PageHero
        variant="split"
        eyebrow="Channel analytics"
        gradientWord="YouTube"
        title="Growth"
        description="Public stats from the Zyvor channel — refreshed from YouTube Data API via our backend cache."
        primaryCta={{label: 'Watch demos', to: '/demo'}}
        secondaryCta={{label: 'Schedule a demo', to: '/contact?intent=demo&utm_source=youtube&utm_medium=page'}}
      />

      <PageContent>
        <div className={styles.youtubePage}>
          {loading && <div className={styles.emptyState}>Loading channel stats…</div>}

          {!loading && error && (
            <div className={styles.emptyState}>
              Could not load YouTube stats ({error}). Try again later or visit <Link to="/demo">product demos</Link>.
            </div>
          )}

          {!loading && !error && data && !data.configured && (
            <div className={styles.emptyState}>
              YouTube stats are not configured on this server yet. Product demos are still available on the{' '}
              <Link to="/demo">demo page</Link>.
            </div>
          )}

          {!loading && !error && data?.configured && channel && (
            <>
              <div className={styles.statRow}>
                <div className={styles.statCard}>
                  <div className={styles.statLabel}>Subscribers</div>
                  <div className={styles.statValue}>{formatYouTubeCount(channel.subscriberCount)}</div>
                </div>
                <div className={styles.statCard}>
                  <div className={styles.statLabel}>Total views</div>
                  <div className={styles.statValue}>{formatYouTubeCount(channel.viewCount)}</div>
                </div>
                <div className={styles.statCard}>
                  <div className={styles.statLabel}>Videos published</div>
                  <div className={styles.statValue}>{formatYouTubeCount(channel.videoCount)}</div>
                </div>
                <div className={styles.statCard}>
                  <div className={styles.statLabel}>Channel</div>
                  <div className={styles.statValue} style={{fontSize: '1.1rem'}}>
                    {channel.customUrl || channel.title}
                  </div>
                </div>
              </div>

              {data.updatedAt && (
                <p className={styles.metaLine}>
                  Last refreshed {new Date(data.updatedAt).toLocaleString()}
                  {data.error ? ` · sync warning: ${data.error}` : ''}
                </p>
              )}

              {milestones.length > 0 && (
                <section className={styles.sectionBlock}>
                  <SectionHeader eyebrow="Growth" title="Subscriber milestones reached" />
                  <div className={styles.milestoneRow}>
                    {milestones.map((m) => (
                      <span key={m} className={styles.milestonePill}>
                        {formatYouTubeCount(m)}+
                      </span>
                    ))}
                  </div>
                </section>
              )}

              {!!data.featuredVideos?.length && (
                <section className={styles.sectionBlock}>
                  <SectionHeader
                    eyebrow="Product demos"
                    title="Featured demo performance"
                    subtitle="HyperSDK migration and GuestKit walkthrough videos embedded across the site."
                  />
                  <VideoGrid videos={data.featuredVideos} />
                </section>
              )}

              {!!data.migrationVideos?.length && (
                <section className={styles.sectionBlock}>
                  <SectionHeader
                    eyebrow="Migration content"
                    title="VMware & migration videos"
                    subtitle="Top-performing uploads tagged by migration-related keywords."
                  />
                  <VideoGrid videos={data.migrationVideos} />
                </section>
              )}

              {!!data.latestVideos?.length && (
                <section className={styles.sectionBlock}>
                  <SectionHeader eyebrow="Latest" title="Recent uploads" />
                  <VideoGrid videos={data.latestVideos} />
                </section>
              )}

              {!!data.topVideos?.length && (
                <section className={styles.sectionBlock}>
                  <SectionHeader eyebrow="Top performers" title="Most viewed videos" />
                  <VideoGrid videos={data.topVideos} />
                </section>
              )}

              {!!data.playlists?.length && (
                <section className={styles.sectionBlock}>
                  <SectionHeader eyebrow="Playlists" title="Product playlist stats" />
                  <div className={styles.playlistList}>
                    {data.playlists.map((pl) => (
                      <div key={pl.id} className={styles.playlistItem}>
                        <span>{pl.title}</span>
                        <span>{pl.videoCount} videos</span>
                      </div>
                    ))}
                  </div>
                </section>
              )}
            </>
          )}
        </div>

        <CTASection
          title="See the platform live"
          subtitle="Book a guided demo tailored to your hypervisor mix and migration timeline."
          primaryCta={{label: 'Schedule a Demo', to: '/contact?intent=demo&utm_source=youtube&utm_medium=page'}}
          secondaryCta={{label: 'Watch demos', to: '/demo'}}
        />
      </PageContent>
    </ProductPage>
  );
}
