const runningTypes = new Set([
  'run',
  'running',
  'trailrun',
  'treadmill',
  'virtualrun',
]);

const cyclingTypes = new Set([
  'cycling',
  'ride',
  'virtualride',
  'gravelride',
  'mountainbikeride',
  'emountainbikeride',
  'ebikeride',
  'handcycle',
  'velomobile',
]);

export const isCyclingActivity = (activity: {
  type?: string;
  sport_type?: string;
  subtype?: string;
}) => {
  const values = [activity.type, activity.sport_type, activity.subtype].map(
    (value) => (value ?? '').toLowerCase().replace(/[^a-z0-9]/g, '')
  );
  if (
    values.some((value) => cyclingTypes.has(value)) &&
    values.some((value) => runningTypes.has(value))
  ) {
    return false;
  }

  const activityType =
    activity.sport_type || activity.subtype || activity.type || '';
  return cyclingTypes.has(activityType.toLowerCase().replace(/[^a-z0-9]/g, ''));
};
