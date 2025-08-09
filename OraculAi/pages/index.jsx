import dynamic from "next/dynamic";
const OraculAi = dynamic(() => import("../src/OraculAi"), { ssr: false });

export default function Home() {
  return <OraculAi />;
}
