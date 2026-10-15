import { Link } from "react-router-dom";
import { buttonClasses } from "../components/ui/Button";
import { Container } from "../components/layout/Page";

export default function NotFoundPage() {
  return (
    <Container className="flex flex-col items-center py-24 text-center">
      <p className="font-mono text-sm text-accent">error[runtime]: page not found</p>
      <h1 className="mt-3 text-3xl font-semibold tracking-tight">This page doesn't exist</h1>
      <Link to="/" className={`${buttonClasses("primary")} mt-6`}>
        Back to the overview
      </Link>
    </Container>
  );
}
