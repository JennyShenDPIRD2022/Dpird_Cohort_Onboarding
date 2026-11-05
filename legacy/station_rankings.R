# Rank each station's monthly rainfall using base R only.
config_lines <- readLines("config.yaml", warn = FALSE)
daily_line <- grep("daily_weather:", config_lines, value = TRUE)
output_line <- grep("station_rankings:", config_lines, value = TRUE)
daily_path <- trimws(sub("daily_weather:", "", daily_line, fixed = TRUE))
output_path <- trimws(sub("station_rankings:", "", output_line, fixed = TRUE))

weather <- read.csv(daily_path, stringsAsFactors = FALSE)
weather$date <- as.Date(weather$date)
weather <- weather[!duplicated(weather[c("station_id", "date")], fromLast = TRUE), ]
weather$month <- format(weather$date, "%Y-%m")

monthly <- aggregate(
  rainfall_mm ~ month + station_id + station + region,
  data = weather,
  FUN = function(values) sum(values, na.rm = TRUE)
)
monthly$rank <- ave(
  -monthly$rainfall_mm,
  monthly$month,
  FUN = function(values) rank(values, ties.method = "min")
)
monthly <- monthly[order(monthly$month, monthly$rank, monthly$station), ]

dir.create(dirname(output_path), recursive = TRUE, showWarnings = FALSE)
write.csv(monthly, output_path, row.names = FALSE)