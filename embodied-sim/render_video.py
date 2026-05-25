#!/usr/bin/env python3
"""render_video.py — Compile MuJoCo frames to MP4 for Telegram sharing."""
import os, argparse, numpy as np

def write_video(frames, path, fps=30):
    """Write frames (H,W,3 uint8) to MP4 using imageio."""
    try:
        import imageio
        imageio.mimwrite(path, frames, fps=fps, codec="libx264", quality=8)
        print(f"Video saved: {path}")
    except ImportError:
        print("imageio not installed. Try: pip install imageio[ffmpeg]")
        raise

def write_gif(frames, path, fps=10):
    """Fallback: write frames to GIF (works without ffmpeg)."""
    try:
        from PIL import Image
        imgs = [Image.fromarray(f) for f in frames]
        duration_ms = int(1000 / fps)
        imgs[0].save(path, save_all=True, append_images=imgs[1:], duration=duration_ms, loop=0)
        print(f"GIF saved: {path}")
    except ImportError:
        print("Pillow not installed. Try: pip install Pillow")
        raise


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--frames-file", help="Numpy .npz file with 'frames' array")
    p.add_argument("--output", default="/tmp/safety_run.mp4", help="Output path")
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--gif", action="store_true", help="Output GIF instead of MP4")
    args = p.parse_args()

    if args.frames_file:
        arr = np.load(args.frames_file)
        frames = arr["frames"]
    else:
        print("No frames file provided — use --frames-file")
        return

    if args.gif:
        out = args.output.replace(".mp4", ".gif")
        write_gif(frames, out, args.fps)
    else:
        write_video(frames, args.output, args.fps)

if __name__ == "__main__":
    main()
