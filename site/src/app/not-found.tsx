import Link from "next/link";

export default function NotFound() {
  return (
    <div className="max-w-[1400px] mx-auto px-5 md:px-[60px] py-24 md:py-32 text-center">
      <h1 className="font-heading text-6xl md:text-8xl mb-6">
        <span className="gradient-text">404</span>
      </h1>
      <p className="text-xl text-dim mb-8">
        This page doesn&apos;t exist in the stack.
      </p>
      <Link
        href="/"
        className="inline-flex items-center px-6 py-3 rounded-[8px] bg-electric text-bg font-medium hover:bg-electric/90 transition-colors"
      >
        Back to Home
      </Link>
    </div>
  );
}
