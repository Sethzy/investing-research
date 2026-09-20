// Read-only integration of Bird's search and TweetDetail primitives.
// Session cookies arrive on stdin; never argv, logs or persisted configuration.
import { fetchWithTransientRetries, classifyText } from './x-policy.mjs';
import { TwitterClientBase } from './bird-search/lib/twitter-client-base.js';
import { withSearch } from './bird-search/lib/twitter-client-search.js';
import { buildArticleFieldToggles, buildTweetDetailFeatures } from './bird-search/lib/twitter-client-features.js';
import { TWITTER_API_BASE } from './bird-search/lib/twitter-client-constants.js';
import { findTweetInInstructions, mapTweetResult, parseTweetsFromInstructions } from './bird-search/lib/twitter-client-utils.js';
function failure(value) {
  const message = String(value || '');
  const code = /401|403|authenticate|authorization|login/i.test(message) ? 'authentication_failed'
    : /429|rate.limit/i.test(message) ? 'rate_limited' : 'upstream_failed';
  return { success: false, error: code };
}
try {
  let input = '';
  for await (const chunk of process.stdin) input += chunk;
  const request = JSON.parse(input);
  const Client = withSearch(TwitterClientBase);
  const client = new Client({cookies: request.cookies, timeoutMs: 30000, quoteDepth: 1});
  const fetchOnce = client.fetchWithTimeout.bind(client);
  client.fetchWithTimeout = (...args) => fetchWithTransientRetries(fetchOnce, client.sleep.bind(client), ...args);
  let output;
  if (request.operation === 'search') {
    const result = await client.search(request.query, request.count, {maxPages: 5});
    output = result.success ? {success: true, tweets: result.tweets, has_more: Boolean(result.nextCursor)} : failure(result.error);
  } else if (request.operation === 'capture') {
    output = failure();
    for (const id of await client.getTweetDetailQueryIds()) {
      const variables = {focalTweetId: request.tweet_id, with_rux_injections: false, rankingMode: 'Relevance', includePromotedContent: false, withCommunity: true, withQuickPromoteEligibilityTweetFields: true, withBirdwatchNotes: true, withVoice: true};
      const params = new URLSearchParams({variables: JSON.stringify(variables), features: JSON.stringify(buildTweetDetailFeatures()), fieldToggles: JSON.stringify(buildArticleFieldToggles())});
      const response = await client.fetchWithTimeout(`${TWITTER_API_BASE}/${id}/TweetDetail?${params}`, {method:'GET', headers:client.getHeaders()});
      if (!response.ok) { output = failure(String(response.status)); if ([401,403,429].includes(response.status)) break; continue; }
      const data = await response.json();
      const instructions = data.data?.threaded_conversation_with_injections_v2?.instructions;
      const raw = findTweetInInstructions(instructions, request.tweet_id);
      const tweet = raw ? mapTweetResult(raw, {quoteDepth:1, includeRaw:false}) : null;
      if (!tweet) { output = {success:false,error:'post_unavailable'}; continue; }
      Object.assign(tweet, classifyText(raw, tweet));
      output = {success:true,tweets:[tweet],conversation:parseTweetsFromInstructions(instructions,{quoteDepth:1,includeRaw:false})};
      break;
    }
  } else output = failure();
  process.stdout.write(JSON.stringify(output));
} catch { process.stdout.write(JSON.stringify({success:false,error:'upstream_failed'})); }
