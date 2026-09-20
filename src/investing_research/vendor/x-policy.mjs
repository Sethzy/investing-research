// Narrow integration policy; upstream Bird transport remains unchanged.
export async function fetchWithTransientRetries(fetchOnce, sleep, ...args) {
  for (let attempt = 0; attempt < 3; attempt++) {
    const response = await fetchOnce(...args);
    if (!(response.status === 429 || response.status >= 500) || attempt === 2) return response;
    await response.body?.cancel();
    await sleep(250 * (attempt + 1));
  }
}
export function classifyText(raw, tweet) {
  const note = raw.note_tweet?.note_tweet_results?.result;
  const noteText = note?.text || note?.richtext?.text || note?.rich_text?.text;
  const ordinaryComplete = raw.legacy?.truncated !== true && !raw.article && !raw.note_tweet && typeof raw.legacy?.full_text === 'string' && raw.legacy.full_text === tweet.text && !/(?:…|\.\.\.)\s*(?:https:\/\/t\.co\/\S+)?\s*$/.test(tweet.text);
  const noteComplete = !raw.article && typeof noteText === 'string' && noteText.length > 0 && tweet.text === noteText;
  return {textCompleteness: ordinaryComplete || noteComplete ? 'complete' : 'partial', textSource: noteComplete ? 'note_tweet' : 'legacy', sourceTruncated: raw.legacy?.truncated ?? null};
}
