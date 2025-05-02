import Stat from '@/components/Stat';
import useActivities from '@/hooks/useActivities';
import useHover from '@/hooks/useHover';
import { loadSvgComponent } from '@/utils/svgUtils';
import { formatPace } from '@/utils/utils';
import { yearStats } from '@assets/index';
import { lazy, Suspense } from 'react';

const YearStat = ({
  year,
  onClick,
}: {
  year: string;
  onClick: (_year: string) => void;
}) => {
  let { activities: runs, years } = useActivities();
  // for hover
  const [hovered, eventHandlers] = useHover();
  // lazy Component
  const YearSVG = lazy(() => loadSvgComponent(yearStats, `./year_${year}.svg`));

  if (years.includes(year)) {
    runs = runs.filter((run) => run.start_date_local.slice(0, 4) === year);
  }
  let sumDistance = 0;
  let streak = 0;
  let sumElevationGain = 0;
  let pace = 0; // eslint-disable-line no-unused-vars
  let paceNullCount = 0; // eslint-disable-line no-unused-vars
  let heartRate = 0;
  let heartRateNullCount = 0;
  let totalMetersAvail = 0;
  let totalSecondsAvail = 0;
  runs.forEach((run) => {
    sumDistance += run.distance || 0;
  });
  runs
    .filter((run) => run.type === 'Run')
    .forEach((run) => {
      // sumDistance += run.distance || 0;
      sumElevationGain += run.elevation_gain || 0;
      if (run.average_speed) {
        pace += run.average_speed;
        totalMetersAvail += run.distance || 0;
        totalSecondsAvail += (run.distance || 0) / run.average_speed;
      } else {
        paceNullCount++;
      }
      if (run.average_heartrate) {
        heartRate += run.average_heartrate;
      } else {
        heartRateNullCount++;
      }
      if (run.streak) {
        streak = Math.max(streak, run.streak);
      }
    });
  sumDistance = parseFloat((sumDistance / 1000.0).toFixed(1));
  sumElevationGain = sumElevationGain.toFixed(0);

  const runLengths = runs.filter((run) => run.type === 'Run').length;
  const walkLengths = runs.filter((run) => run.type === 'Walk').length;

  const runDistance = runs
    .filter((run) => run.type === 'Run')
    .reduce((acc, run) => acc + run.distance / 1000, 0)
    .toFixed(1);
  const walkDistance = runs
    .filter((run) => run.type === 'Walk')
    .reduce((acc, run) => acc + run.distance / 1000, 0)
    .toFixed(1);
  const avgPace = formatPace(totalMetersAvail / totalSecondsAvail);
  const avgHeartRate = (heartRate / (runLengths - heartRateNullCount)).toFixed(
    0
  );

  return (
    <div
      className="cursor-pointer"
      onClick={() => onClick(year)}
      {...eventHandlers}
    >
      <section>
        <Stat value={year} description=" Journey" />
        <div className="flex flex-row gap-4">
          <Stat value={runs.length} description=" Total" />
          <Stat value={sumDistance} description=" KM" />
        </div>
        <div className="flex flex-row gap-4">
          <Stat value={runLengths} description=" Runs" />
          <Stat value={runDistance} description=" KM" />
        </div>
        <div className="flex flex-row gap-4">
          <Stat value={walkLengths} description=" Walks" />
          <Stat value={walkDistance} description=" KM" />
        </div>

        <Stat value={avgPace} description=" Run Avg Pace" />
        <Stat value={sumElevationGain} description=" Elevation Gain" />

        <Stat value={`${streak} day`} description=" Streak" />

        <Stat value={avgHeartRate} description=" Run Avg Heart Rate" />
      </section>
      {year !== 'Total' && (
        <Suspense fallback="loading...">
          <YearSVG className="my-4 h-4/6 w-4/6 border-0 p-0" />
        </Suspense>
      )}
      <hr color="red" />
    </div>
  );
};

export default YearStat;
