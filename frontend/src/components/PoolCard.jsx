import React, { useState, useEffect } from 'react';

function PoolCard({ pool, status, onAction }) {
  const [, forceUpdate] = useState(0);
  
  useEffect(() => {
    const interval = setInterval(() => {
      forceUpdate(n => n + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const now = new Date();
  const isFiltering = status.filtering || status.manual_override;
  
  const getStateInfo = () => {
    if (status.manual_override) {
      return { state: 'manual', label: 'Manual', icon: 'play_arrow' };
    } else if (status.filtering) {
      return { state: 'filtering', label: 'Filtering', icon: 'water' };
    } else if (status.next_filter) {
      return { state: 'scheduled', label: 'Scheduled', icon: 'schedule' };
    }
    return { state: 'stopped', label: 'Stopped', icon: 'stop' };
  };

  const stateInfo = getStateInfo();
  const progress = getProgress(stateInfo.state);
  const circumference = 2 * Math.PI * 42;
  const strokeDashoffset = circumference * (1 - progress / 100);

  function getProgress(state) {
    if (state === 'filtering' || state === 'manual') {
      if (status.remaining_minutes != null) {
        return Math.max(0, 100 - (status.remaining_minutes / 60) * 100);
      }
      return 100;
    }
    return state === 'scheduled' ? 10 : 0;
  }

  const getTimeInfo = () => {
    const nowMinutes = now.getHours() * 60 + now.getMinutes();
    
    if (isFiltering && status.started_at) {
      const startedAt = new Date(status.started_at);
      const duration = getCurrentDuration();
      const totalSeconds = duration ? parseDurationToSeconds(duration) : null;
      
      if (totalSeconds) {
        const elapsedSeconds = Math.floor((now - startedAt) / 1000);
        const remainingSeconds = Math.max(0, totalSeconds - elapsedSeconds);
        const remainingMins = Math.floor(remainingSeconds / 60);
        const remainingSecs = remainingSeconds % 60;
        
        const endsAt = new Date(startedAt.getTime() + totalSeconds * 1000);
        const endTime = `${endsAt.getHours().toString().padStart(2, '0')}:${endsAt.getMinutes().toString().padStart(2, '0')}`;
        
        let remainingDisplay;
        if (remainingMins >= 60) {
          const hours = Math.floor(remainingMins / 60);
          const mins = remainingMins % 60;
          remainingDisplay = `${hours}h ${mins.toString().padStart(2, '0')}m`;
        } else {
          remainingDisplay = `${remainingMins}:${remainingSecs.toString().padStart(2, '0')}`;
        }
        
        return {
          label: 'Active',
          time: `Ends at ${endTime}`,
          remaining: remainingSeconds > 0 ? remainingDisplay : null
        };
      }
      
      const endsAt = new Date(startedAt.getTime() + 3 * 60 * 60 * 1000);
      const endTime = `${endsAt.getHours().toString().padStart(2, '0')}:${endsAt.getMinutes().toString().padStart(2, '0')}`;
      return {
        label: 'Active',
        time: `Ends at ${endTime}`,
        remaining: null
      };
    }
    
    if (status.remaining_minutes != null && status.remaining_minutes > 0) {
      const mins = status.remaining_minutes;
      let remainingDisplay;
      if (mins >= 60) {
        const hours = Math.floor(mins / 60);
        const remainingMins = mins % 60;
        remainingDisplay = `${hours}h ${remainingMins.toString().padStart(2, '0')}m`;
      } else {
        remainingDisplay = `${mins}m`;
      }
      return {
        label: 'Active',
        time: status.ends_at ? `Ends at ${status.ends_at}` : 'Filtering',
        remaining: remainingDisplay
      };
    }
    
    if (status.next_filter) {
      const nextMinutes = parseTimeToMinutes(status.next_filter);
      let minutesUntil = nextMinutes - nowMinutes;
      if (minutesUntil < 0) minutesUntil += 24 * 60;
      
      const hoursUntil = Math.floor(minutesUntil / 60);
      const minsUntil = minutesUntil % 60;
      
      let timeText = '';
      if (hoursUntil > 0) {
        timeText = `Next in ${hoursUntil}h ${minsUntil}m`;
      } else if (minsUntil > 0) {
        timeText = `Next in ${minsUntil}m`;
      } else {
        timeText = 'Starting...';
      }
      
      return { label: 'Next', time: timeText, remaining: null };
    }
    
    if (status.last_filtered) {
      return { label: 'Idle', time: `Last filtered ${status.last_filtered}`, remaining: null };
    }
    
    return { label: 'Idle', time: '', remaining: null };
  }

  const timeInfo = getTimeInfo();

  function getCurrentDuration() {
    if (!pool.schedule || pool.schedule.length === 0) return null;
    
    const nowMinutes = now.getHours() * 60 + now.getMinutes();
    
    for (const entry of pool.schedule) {
      const startMinutes = parseTimeToMinutes(entry.startAt);
      const durationSeconds = parseDurationToSeconds(entry.duration);
      let endMinutes = startMinutes + Math.floor(durationSeconds / 60);
      
      if (endMinutes > 24 * 60) {
        let effectiveNow = nowMinutes;
        if (effectiveNow < startMinutes) effectiveNow += 24 * 60;
        
        const effectiveEnd = endMinutes % (24 * 60);
        const adjustedStart = startMinutes;
        
        if (effectiveNow >= adjustedStart && effectiveNow < effectiveEnd) {
          return entry.duration;
        }
      } else {
        if (nowMinutes >= startMinutes && nowMinutes < endMinutes) {
          return entry.duration;
        }
      }
    }
    return null;
  }

  function parseTimeToMinutes(timeStr) {
    const [h, m] = timeStr.split(':').map(Number);
    return h * 60 + m;
  }

  function parseDurationToSeconds(duration) {
    let totalSeconds = 0;
    const hourMatch = duration.match(/(\d+)h/);
    const minMatch = duration.match(/(\d+)m/);
    
    if (hourMatch) totalSeconds += parseInt(hourMatch[1]) * 3600;
    if (minMatch) totalSeconds += parseInt(minMatch[1]) * 60;
    
    if (!hourMatch && !minMatch) {
      totalSeconds = parseInt(duration) * 3600;
    }
    
    return totalSeconds;
  }

  function formatTime(date) {
    return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
  }

  const hasManualOverride = status.manual_override != null;
  const canStart = !isFiltering && !hasManualOverride;
  const canStop = isFiltering || hasManualOverride;

  return (
    <div className="pool-card">
      <div className="pool-header">
        <div className="pool-info">
          <h2>{pool.name}</h2>
          <div className="location">{pool.location}</div>
        </div>
        <div className={`pool-status-chip ${stateInfo.state}`}>
          <span className="material-symbols-rounded">{stateInfo.icon}</span>
          {stateInfo.label}
        </div>
      </div>

      <div className="pool-body">
        <div className="status-ring-container">
          <div className="status-ring">
            <svg width="100" height="100" viewBox="0 0 100 100">
              <circle className="bg" cx="50" cy="50" r="42" />
              <circle 
                className={`progress ${stateInfo.state}`}
                cx="50" 
                cy="50" 
                r="42"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
              />
            </svg>
            <div className="status-ring-content">
              <span className="material-symbols-rounded">{stateInfo.icon}</span>
              <div className="progress-text">{stateInfo.label}</div>
            </div>
          </div>
        </div>

        <div className="status-details">
          <div className="status-label">{timeInfo.label}</div>
          <div className="status-time">{timeInfo.time}</div>
          {timeInfo.remaining && (
            <div className="status-remaining">{timeInfo.remaining}</div>
          )}
        </div>

        {pool.schedule && pool.schedule.length > 0 && (
          <div className="schedule-section">
            <div className="schedule-title">Schedule</div>
            <ul className="schedule-list">
              {pool.schedule.map((entry, idx) => (
                <ScheduleItem 
                  key={idx} 
                  entry={entry} 
                  now={now} 
                  isFiltering={isFiltering}
                  startedAt={status.started_at}
                />
              ))}
            </ul>
          </div>
        )}

        <div className="pool-actions">
          <button 
            className="action-button primary"
            disabled={!canStart}
            onClick={() => onAction(pool.id, 'start')}
          >
            <span className="material-symbols-rounded">play_arrow</span>
            Start
          </button>
          <button 
            className="action-button secondary"
            disabled={!canStop}
            onClick={() => onAction(pool.id, 'stop')}
          >
            <span className="material-symbols-rounded">stop</span>
            Stop
          </button>
          {hasManualOverride && (
            <button 
              className="action-button secondary"
              onClick={() => onAction(pool.id, 'resume')}
            >
              <span className="material-symbols-rounded">schedule</span>
              Resume
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function ScheduleItem({ entry, now, isFiltering, startedAt }) {
  const timeMinutes = parseTimeToMinutes(entry.startAt);
  const durationSeconds = parseDurationToSeconds(entry.duration);
  const endMinutes = timeMinutes + Math.floor(durationSeconds / 60);
  
  const currentMinutes = now.getHours() * 60 + now.getMinutes();
  
  let isActive = false;
  if (isFiltering && startedAt) {
    const startedAtDate = new Date(startedAt);
    const startedMinutes = startedAtDate.getHours() * 60 + startedAtDate.getMinutes();
    const elapsedMinutes = Math.floor((now - startedAtDate) / 60000);
    
    isActive = elapsedMinutes >= 0 && elapsedMinutes < Math.floor(durationSeconds / 60);
  } else {
    isActive = currentMinutes >= timeMinutes && currentMinutes < endMinutes;
  }

  function parseTimeToMinutes(timeStr) {
    const [h, m] = timeStr.split(':').map(Number);
    return h * 60 + m;
  }

  function parseDurationToSeconds(duration) {
    let totalSeconds = 0;
    const hourMatch = duration.match(/(\d+)h/);
    const minMatch = duration.match(/(\d+)m/);
    
    if (hourMatch) totalSeconds += parseInt(hourMatch[1]) * 3600;
    if (minMatch) totalSeconds += parseInt(minMatch[1]) * 60;
    
    if (!hourMatch && !minMatch) {
      totalSeconds = parseInt(duration) * 3600;
    }
    
    return totalSeconds;
  }

  return (
    <li className={`schedule-item ${isActive ? 'active' : ''}`}>
      <span className="time">{entry.startAt}</span>
      <span className="duration">{entry.duration}</span>
    </li>
  );
}

export default PoolCard;
