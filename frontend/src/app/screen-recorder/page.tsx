"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  CheckCircle2,
  Download,
  Mic,
  MicOff,
  MonitorUp,
  Pause,
  Play,
  RotateCcw,
  Square,
  Video,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";

type RecorderState = "idle" | "recording" | "paused" | "ready";

export default function ScreenRecorderPage() {
  const [recorderState, setRecorderState] = useState<RecorderState>("idle");
  const [includeMic, setIncludeMic] = useState(true);
  const [error, setError] = useState("");
  const [elapsedMs, setElapsedMs] = useState(0);
  const [videoUrl, setVideoUrl] = useState("");
  const [fileSize, setFileSize] = useState(0);

  const previewRef = useRef<HTMLVideoElement | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<number | null>(null);
  const startedAtRef = useRef(0);
  const accumulatedMsRef = useRef(0);
  const chunksRef = useRef<BlobPart[]>([]);

  const isActive = recorderState === "recording" || recorderState === "paused";
  const elapsedLabel = useMemo(() => formatDuration(elapsedMs), [elapsedMs]);

  useEffect(() => {
    return () => {
      stopTimer();
      stopTracks();
      if (videoUrl) URL.revokeObjectURL(videoUrl);
    };
  }, [videoUrl]);

  async function startRecording() {
    setError("");
    setFileSize(0);
    if (videoUrl) {
      URL.revokeObjectURL(videoUrl);
      setVideoUrl("");
    }

    if (!navigator.mediaDevices?.getDisplayMedia || typeof MediaRecorder === "undefined") {
      setError("Screen recording is not supported in this browser. Use Chrome, Edge, or another Chromium browser.");
      return;
    }

    try {
      const displayStream = await navigator.mediaDevices.getDisplayMedia({
        video: { frameRate: 30 },
        audio: true,
      });

      const tracks = [...displayStream.getVideoTracks(), ...displayStream.getAudioTracks()];

      if (includeMic) {
        try {
          const micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
          tracks.push(...micStream.getAudioTracks());
        } catch {
          setError("Microphone was not added. Recording will continue with screen audio only.");
        }
      }

      const combinedStream = new MediaStream(tracks);
      streamRef.current = combinedStream;
      chunksRef.current = [];

      if (previewRef.current) {
        previewRef.current.srcObject = combinedStream;
        await previewRef.current.play().catch(() => undefined);
      }

      const mimeType = getSupportedMimeType();
      const recorder = new MediaRecorder(combinedStream, mimeType ? { mimeType } : undefined);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "video/webm" });
        const nextUrl = URL.createObjectURL(blob);
        setVideoUrl(nextUrl);
        setFileSize(blob.size);
        setRecorderState("ready");
        stopTimer();
        stopTracks();
        if (previewRef.current) previewRef.current.srcObject = null;
      };

      combinedStream.getVideoTracks()[0]?.addEventListener("ended", () => {
        if (mediaRecorderRef.current?.state !== "inactive") stopRecording();
      });

      accumulatedMsRef.current = 0;
      startedAtRef.current = Date.now();
      setElapsedMs(0);
      startTimer();
      recorder.start(1000);
      setRecorderState("recording");
    } catch (err) {
      if (err instanceof DOMException && err.name === "NotAllowedError") {
        setError("Screen selection was cancelled or blocked.");
      } else {
        setError(err instanceof Error ? err.message : "Could not start screen recording.");
      }
      stopTracks();
    }
  }

  function pauseRecording() {
    const recorder = mediaRecorderRef.current;
    if (!recorder || recorder.state !== "recording") return;
    recorder.pause();
    accumulatedMsRef.current += Date.now() - startedAtRef.current;
    stopTimer();
    setRecorderState("paused");
  }

  function resumeRecording() {
    const recorder = mediaRecorderRef.current;
    if (!recorder || recorder.state !== "paused") return;
    recorder.resume();
    startedAtRef.current = Date.now();
    startTimer();
    setRecorderState("recording");
  }

  function stopRecording() {
    const recorder = mediaRecorderRef.current;
    if (!recorder || recorder.state === "inactive") {
      stopTracks();
      return;
    }

    if (recorder.state === "recording") {
      accumulatedMsRef.current += Date.now() - startedAtRef.current;
      setElapsedMs(accumulatedMsRef.current);
    }

    recorder.stop();
  }

  function resetRecording() {
    if (videoUrl) URL.revokeObjectURL(videoUrl);
    setVideoUrl("");
    setFileSize(0);
    setElapsedMs(0);
    setError("");
    setRecorderState("idle");
  }

  function startTimer() {
    stopTimer();
    timerRef.current = window.setInterval(() => {
      setElapsedMs(accumulatedMsRef.current + Date.now() - startedAtRef.current);
    }, 250);
  }

  function stopTimer() {
    if (timerRef.current) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }

  function stopTracks() {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
  }

  return (
    <div className="-m-6 min-h-full bg-slate-50 p-4 text-slate-950 md:p-6">
      <div className="mx-auto grid max-w-[1280px] gap-4 xl:grid-cols-[minmax(0,1fr)_360px]">
        <section className="space-y-4">
          <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <Badge className="bg-indigo-100 text-indigo-700 hover:bg-indigo-100">
              Screen Recorder
            </Badge>
            <h1 className="mt-3 text-2xl font-bold tracking-tight md:text-4xl">
              Record your screen and download the video.
            </h1>
            <p className="mt-2 max-w-3xl text-sm text-slate-600 md:text-base">
              Capture a tab, window, or full screen for product research clips, supplier pages,
              and quick walkthroughs. Recordings stay in your browser until you download them.
            </p>
          </div>

          <Card className="border-slate-200 bg-white shadow-sm">
            <CardHeader className="flex flex-row items-center justify-between gap-3 space-y-0">
              <CardTitle className="flex items-center gap-2 text-lg">
                <Video className="h-5 w-5 text-indigo-600" />
                Recorder
              </CardTitle>
              <Badge variant={recorderState === "recording" ? "danger" : recorderState === "ready" ? "success" : "secondary"}>
                {recorderState}
              </Badge>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="overflow-hidden rounded-lg border border-slate-200 bg-slate-950">
                {videoUrl ? (
                  <video src={videoUrl} controls className="aspect-video w-full bg-slate-950" />
                ) : (
                  <video ref={previewRef} muted playsInline className="aspect-video w-full bg-slate-950" />
                )}
              </div>

              {error && (
                <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
                  {error}
                </div>
              )}

              <div className="flex flex-col gap-3 rounded-lg bg-slate-50 p-3 md:flex-row md:items-center md:justify-between">
                <div>
                  <p className="text-xs font-semibold uppercase text-slate-500">Duration</p>
                  <p className="font-mono text-2xl font-bold text-slate-950">{elapsedLabel}</p>
                </div>
                <div className="flex items-center gap-3">
                  {includeMic ? <Mic className="h-4 w-4 text-emerald-600" /> : <MicOff className="h-4 w-4 text-slate-400" />}
                  <span className="text-sm text-slate-700">Microphone</span>
                  <Switch checked={includeMic} onCheckedChange={setIncludeMic} disabled={isActive} />
                </div>
              </div>

              <div className="flex flex-wrap gap-2">
                {recorderState === "idle" || recorderState === "ready" ? (
                  <Button onClick={startRecording} className="bg-indigo-600 text-white hover:bg-indigo-700">
                    <MonitorUp className="mr-2 h-4 w-4" />
                    Start Recording
                  </Button>
                ) : null}

                {recorderState === "recording" ? (
                  <Button variant="outline" onClick={pauseRecording}>
                    <Pause className="mr-2 h-4 w-4" />
                    Pause
                  </Button>
                ) : null}

                {recorderState === "paused" ? (
                  <Button variant="outline" onClick={resumeRecording}>
                    <Play className="mr-2 h-4 w-4" />
                    Resume
                  </Button>
                ) : null}

                {isActive ? (
                  <Button variant="destructive" onClick={stopRecording}>
                    <Square className="mr-2 h-4 w-4" />
                    Stop
                  </Button>
                ) : null}

                {videoUrl ? (
                  <>
                    <Button asChild variant="outline">
                      <a href={videoUrl} download={`screen-recording-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-")}.webm`}>
                        <Download className="mr-2 h-4 w-4" />
                        Download
                      </a>
                    </Button>
                    <Button variant="ghost" onClick={resetRecording}>
                      <RotateCcw className="mr-2 h-4 w-4" />
                      Reset
                    </Button>
                  </>
                ) : null}
              </div>
            </CardContent>
          </Card>
        </section>

        <aside className="space-y-4">
          <Card className="border-slate-200 bg-white shadow-sm">
            <CardHeader>
              <CardTitle className="text-lg">Quick Checks</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-slate-600">
              <CheckItem text="Choose a Chrome tab when recording product videos." />
              <CheckItem text="Turn microphone on only when you want voice notes." />
              <CheckItem text="Click Stop sharing or Stop to finish the file." />
              <Separator />
              <div>
                <p className="font-semibold text-slate-900">File size</p>
                <p>{fileSize ? formatBytes(fileSize) : "No recording downloaded yet."}</p>
              </div>
            </CardContent>
          </Card>

          <Card className="border-indigo-200 bg-indigo-50 shadow-sm">
            <CardContent className="space-y-2 p-4 text-sm text-indigo-950">
              <p className="font-semibold">Best use for WeChat links</p>
              <p>Open the product video manually, start recording this page, then choose the WeChat window or browser tab in the picker.</p>
            </CardContent>
          </Card>
        </aside>
      </div>
    </div>
  );
}

function CheckItem({ text }: { text: string }) {
  return (
    <div className="flex gap-2">
      <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" />
      <span>{text}</span>
    </div>
  );
}

function getSupportedMimeType() {
  const types = [
    "video/webm;codecs=vp9,opus",
    "video/webm;codecs=vp8,opus",
    "video/webm",
  ];
  return types.find((type) => MediaRecorder.isTypeSupported(type)) || "";
}

function formatDuration(ms: number) {
  const totalSeconds = Math.floor(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60).toString().padStart(2, "0");
  const seconds = (totalSeconds % 60).toString().padStart(2, "0");
  return `${minutes}:${seconds}`;
}

function formatBytes(bytes: number) {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  return `${(bytes / 1024 ** index).toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}
