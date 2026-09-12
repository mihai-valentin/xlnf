// XLNF — posthog.js
// PostHog init for the /notes/ layer.
//
// index.html inlines this same init in <head> so its pageview fires before first
// paint. Notes load it deferred instead: a content page doesn't need the pageview
// that early, and one shared file beats pasting the snippet into every note.
// Config must stay in sync with the inlined copy in index.html.

!function(t,e){var o,n,p,r;e.__SV||(window.posthog && window.posthog.__loaded)||(window.posthog=e,e._i=[],e.init=function(i,s,a){function g(t,e){var o=e.split(".");2==o.length&&(t=t[o[0]],e=o[1]),t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}}(p=t.createElement("script")).type="text/javascript",p.crossOrigin="anonymous",p.async=!0,p.src=s.api_host.replace(".i.posthog.com","-assets.i.posthog.com")+"/static/array.js",(r=t.getElementsByTagName("script")[0]).parentNode.insertBefore(p,r);var u=e;for(void 0!==a?u=e[a]=[]:a="posthog",u.people=u.people||[],u.toString=function(t){var e="posthog";return"posthog"!==a&&(e+="."+a),t||(e+=" (stub)"),e},u.people.toString=function(){return u.toString(1)+".people (stub)"},o="Ir init Br Zr Ci jr $r Lr capture calculateEventProperties Yr register register_once register_for_session unregister unregister_for_session Jr getFeatureFlag getFeatureFlagPayload getFeatureFlagResult isFeatureEnabled reloadFeatureFlags updateFlags updateEarlyAccessFeatureEnrollment getEarlyAccessFeatures on onFeatureFlags onSurveysLoaded onSessionId getSurveys getActiveMatchingSurveys renderSurvey displaySurvey cancelPendingSurvey canRenderSurvey canRenderSurveyAsync Kr identify setPersonProperties group resetGroups setPersonPropertiesForFlags resetPersonPropertiesForFlags setGroupPropertiesForFlags resetGroupPropertiesForFlags reset setIdentity clearIdentity get_distinct_id getGroups get_session_id get_session_replay_url alias set_config startSessionRecording stopSessionRecording sessionRecordingStarted captureException captureLog startExceptionAutocapture stopExceptionAutocapture loadToolbar get_property getSessionProperty Wr zr createPersonProfile setInternalOrTestUser Xr Or en opt_in_capturing opt_out_capturing has_opted_in_capturing has_opted_out_capturing get_explicit_consent_status is_capturing clear_opt_in_out_capturing Vr debug ki Gr getPageViewId captureTraceFeedback captureTraceMetric Nr".split(" "),n=0;n<o.length;n++)g(u,o[n]);e._i.push([i,s,a])},e.__SV=1)}(document,window.posthog||[]);

posthog.init('phc_CB5LFj3crsxvKs9tn7wVoc5TpwEBrPVyPkhGUseaKeEw', {
  api_host: 'https://eu.i.posthog.com',
  defaults: '2026-01-30',
  person_profiles: 'identified_only',
  // No cookies, but this IS storage on the device: tab-scoped, wiped on tab
  // close. Chosen over 'memory' because memory mints a new distinct ID on every
  // navigation, so sessions never stitch across pages. See README → Analytics.
  persistence: 'sessionStorage',
  autocapture: false,               // manual events only
  capture_pageview: true,
  disable_session_recording: true,
  disable_surveys: true,            // we ship no surveys — skip surveys.js
  capture_dead_clicks: false,       // autocapture is off; skip dead-clicks-autocapture.js
  capture_performance: false,       // skip web-vitals-with-attribution.js
});
