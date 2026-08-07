import { computeChart } from "/Users/switchaphon/ghq/github.com/switchaphon/leica-oracle/plugins/maw-duang/src/index";
import { RASI, RASI_LORD, GRAHAS, BHAVA, toThaiNum, fmtDeg } from "/Users/switchaphon/ghq/github.com/switchaphon/leica-oracle/plugins/maw-duang/src/thai";
import * as S from "/Users/switchaphon/ghq/github.com/switchaphon/leica-oracle/plugins/maw-duang/src/siam";
import { readNatal, renderReading } from "/Users/switchaphon/ghq/github.com/switchaphon/leica-oracle/plugins/maw-duang/src/read";
(globalThis as any).MawDuang = { computeChart, RASI, RASI_LORD, GRAHAS, BHAVA, toThaiNum, fmtDeg, S, readNatal, renderReading };
